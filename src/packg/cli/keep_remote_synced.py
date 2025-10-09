"""
Keep a remote git repository synced, without having to commit.

Notes:
    - The script will not delete anything in the target, it will only upload added or changed files.
      So when renaming or deleting files you will get leftovers.
    - After locally pushing, git will get confused on the target system, so you will need to either:
        1. reset the index forward to match the files, or
        2. hard reset the files backward and pull, or
        3. hard reset to current origin or
        4. checkout to remove the changes and pull.

It works by finding files as follows:
    - given `git add --dry-run .` to find files.
       i.e. will ignore using .gitignore, assumes the target repo is on the same git commit state.
    - also by checking all files again that have been synced in the past
    - compares chmod and stat of last synced state and current to determine the delta
    - Requires rsync
"""

import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from timeit import default_timer as timer

from attrs import define
from loguru import logger

from packg import format_exception
from packg.dtime import get_timestamp_for_filename
from packg.iotools.git_status_checker import (
    check_for_stages,
    check_for_unpushed_commits,
    get_gitadd_dryrun_output,
    parse_gitadd_dryrun_output,
)
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.system import systemcall, systemcall_with_assert
from packg.typext import PathType
from typedparser import TypedParser, VerboseQuietArgs, add_argument


@define
class Args(VerboseQuietArgs):
    src_base_dir: str = add_argument(
        shortcut="-s", type=str, help="Source base dir", default="/path/to/source"
    )
    src_list_rel: str = add_argument(
        shortcut="-l",
        type=str,
        default="folder1,folder2",
        help="List of source dirs relative to path, separated by comma.",
    )
    dst: str = add_argument(
        shortcut="-d",
        type=str,
        help="Destination directory.",
        default="user@server:/path/to/target",
    )
    test: bool = add_argument(shortcut="-t", action="store_true", help="Test only.")
    public_chmod: bool = add_argument(
        shortcut="-p", action="store_true", help="Set public file permissions on target."
    )
    wait_time: float = add_argument(
        shortcut="-w",
        type=float,
        default=2.0,
        help="Wait time in seconds before syncing again (0 = only once).",
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)

    out, err, retcode = systemcall("rsync -V")
    assert retcode == 0, f"rsync must be installed, but got: {err}"
    logger.info(f"Using rsync {out.strip().splitlines()[0]}")

    src_base_dir = Path(args.src_base_dir).resolve().absolute()
    logger.info(f"Resolved src_base_dir: {src_base_dir}")
    syncer = SyncCollector(
        src_base_dir, verbose=args.verbose, test=args.test, public_chmod=args.public_chmod
    )
    src_list_rel = args.src_list_rel.split(",")
    wait_time = args.wait_time
    logger.info(f"Will sync {src_list_rel} in {src_base_dir}")

    while True:
        try:
            for src_rel in src_list_rel:
                syncer.collect_from_local_dir(src_rel)
            syncer.run_rsync(args.dst)
            if wait_time <= 0:
                logger.info(f"Running only once.")
                break
            time.sleep(wait_time)
        except (KeyboardInterrupt, AssertionError) as e:
            logger.warning(f"\nInterrupted by user or file changes: {format_exception(e)}")
            break

    syncer.close()  # delete temp dirs


RE_ENTERING = re.compile("Entering '(.*)'")


@dataclass
class SyncCollector:
    src_base_dir: PathType
    verbose: bool = True
    test: bool = False
    public_chmod: bool = False

    def __post_init__(self):
        self.src_base_dir = Path(self.src_base_dir)
        assert (
            self.src_base_dir.is_absolute()
        ), f"src_base_dir must be absolute but is {self.src_base_dir}."
        self._tempdir_obj = tempfile.TemporaryDirectory(prefix="public_remote_sync_")
        self.temp_dir = Path(self._tempdir_obj.name)
        self.reset()

    def reset(self):
        self._files = []
        self.start_dir = Path(os.getcwd())
        self.stored_files = {}
        self.start_timer = None
        self.n_rounds = 0

    def collect_from_local_dir(self, local_dir_rel: PathType):
        local_dir = self.src_base_dir / local_dir_rel
        assert local_dir.is_dir(), f"local_dir {local_dir} must be a directory."
        assert (local_dir / ".git").is_dir(), "Usage without git is not implemented"
        gitadd_output = get_gitadd_dryrun_output(local_dir)
        root_files = parse_gitadd_dryrun_output(
            gitadd_output, local_dir, return_relative_paths=False
        )
        for file, status in root_files.items():
            file_rel = Path(file).relative_to(self.src_base_dir)
            if status == "add":
                self._files.append(file_rel.as_posix())
            elif status == "remove":
                pass
            else:
                raise ValueError(f"Status {status} for {file} unexpected")

        stages = check_for_stages(local_dir)
        # assert stages == "", (
        #     f"Exiting due to staged files in {local_dir}:\n{stages}")
        if stages != "":
            staged_files = [
                (local_dir / f).relative_to(self.src_base_dir).as_posix()
                for f in stages.split("\n")
            ]
            self._files += staged_files
        unpushed = check_for_unpushed_commits(local_dir)
        assert unpushed == "", f"Exiting due to unpushed commits in {local_dir}:\n{unpushed}"

        self._files = sorted(set(self._files))

    def get_all_collected_files(self):
        return self._files

    def find_files_to_update(self):
        in_files = self.get_all_collected_files()
        to_update = []
        for file in in_files:
            full_file = self.src_base_dir / file
            if not full_file.is_file():
                if self.verbose:
                    print(f"    not a file anymore: {file}")
                continue
            stat = full_file.stat()
            modtime = stat.st_mtime
            size = stat.st_size
            if file in self.stored_files:
                old_modtime, old_size = self.stored_files[file]
                if old_modtime == modtime and old_size == size:
                    if self.verbose:
                        print(f"    unchanged: {file}")
                    continue
            to_update.append(file)
            self.stored_files[file] = (modtime, size)
        return to_update

    def run_rsync(self, dst):
        if self.start_timer is None:
            self.start_timer = timer()
        self.n_rounds += 1
        files_to_update = self.find_files_to_update()
        current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        time_delta = timer() - self.start_timer
        current_timedelta_str = time.strftime("%H:%M:%S", time.gmtime(time_delta))

        tstr = f"{current_time_str} running for {current_timedelta_str} (round {self.n_rounds:4d})"

        if len(files_to_update) == 0:
            print(
                f"{tstr}: Nothing to update.",
                end="\n" if self.verbose or self.n_rounds % 100 == 0 else "\r",
            )
            return
        print()
        logger.info(f"Updating {len(files_to_update)} files.")
        for file in files_to_update:
            logger.info(f"    will update: {file}")

        temp_dir = self.temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = temp_dir / f"temp_sync_{get_timestamp_for_filename()}.txt"
        all_lines = files_to_update + [""]
        temp_file.write_text("\n".join(all_lines))

        perms = "D755,F644" if self.public_chmod else "D700,F600"
        other_args = []
        if self.test:
            other_args.append("--dry-run")

        rsync_cmd = (
            f"rsync -av {' '.join(other_args)} --chmod={perms} "
            f"--files-from={temp_file.as_posix()} {self.src_base_dir}/ {dst}/"
        )
        if self.verbose:
            logger.debug(f"$ {rsync_cmd}")
        systemcall_with_assert(rsync_cmd, verbose=self.verbose)
        logger.info(f"    update successful.{' (dry run)' if self.test else ''}")

    def close(self):
        self._tempdir_obj.cleanup()


if __name__ == "__main__":
    main()
