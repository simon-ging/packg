"""
Find duplicate files, shared by the deduplicate_within_dir and deduplicate_between_dirs scripts.

Files are duplicates if their content is the same byte for byte. With the approx method two PDFs
are also duplicates if they hold the same text, e.g. the same document exported twice, which
gives different bytes because of the timestamps inside. Reading the text needs the pdftotext
binary of poppler.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np
from attr import define
from loguru import logger
from natsort import natsorted
from tqdm import tqdm

from packg import Const
from packg.iotools.folder_hash_cache import FolderHashCache, make_index_cached
from packg.iotools.pathspec_matcher import PathSpecArgs, make_and_apply_pathspecs
from packg.tqdmext import tqdm_max_ncols
from typedparser import VerboseQuietArgs, add_argument


class MethodC(Const):
    EXACT = "exact"
    APPROX = "approx"


# with the approx method files are compared if their sizes differ by less than this many bytes
# or by less than this fraction of the smaller one
APPROX_SIZE_DIFF_BYTES = 1024
APPROX_SIZE_DIFF_REL = 0.1
SIZE_COMPARE_CHUNK = 100
# a date in a file name, either at the beginning or after some separator
RE_DATES = [
    re.compile(r"^(20[12]\d[_.-]?\d{2}[_.-]?\d{2})[_.-].*?$"),
    re.compile(r"^.*?[_.-](20[12]\d[_.-]?\d{2}[_.-]?\d{2})[_.-].*?$"),
]


@define(slots=False)
class DedupArgs(PathSpecArgs, VerboseQuietArgs):
    reset_cache: bool = add_argument(shortcut="-r", action="store_true", help="Reset the cache.")
    cache_max_age_hours: float = add_argument(
        shortcut="-c",
        type=float,
        default=24 * 7,
        help="Max age of cache in hours (default 1 week).",
    )
    write: bool = add_argument(shortcut="-w", action="store_true", help="Delete the duplicates.")
    compare_method: str = add_argument(
        shortcut="-m",
        type=str,
        default=MethodC.EXACT,
        help=f"Method to compare files: {', '.join(MethodC.values())}. approx also finds PDFs "
        f"that hold the same text, which needs the pdftotext binary.",
    )
    check_date_in_filename: bool = add_argument(
        shortcut="-d",
        action="store_true",
        help="""\
When comparing files, try to figure out the document date from the filename (e.g.
report_20241003.pdf). Then, when another file has a different date, directly assume they are
different and keep both.""",
    )


@define
class FolderFiles:
    """The files of one folder that take part in the comparison, in natural name order."""

    folder: Path
    names: list[str]
    sizes: np.ndarray
    hashes: FolderHashCache


def load_folder(folder: Path, args: DedupArgs) -> FolderFiles:
    """Index the folder, apply the include and exclude patterns, and open its hash cache."""
    folder = Path(folder)
    index = make_index_cached(
        folder,
        cache_max_age_seconds=args.cache_max_age_hours * 3600,
        reset_cache=args.reset_cache,
    )
    logger.info(f"Found {len(index)} files in {folder} before filtering")
    keys = make_and_apply_pathspecs(
        list(index.keys()),
        args.include_git,
        args.include_regex,
        args.exclude_git,
        args.exclude_regex,
        args.exclude_gitignore_file,
    )
    names = natsorted(keys)
    logger.info(f"{len(names)} files remain after filtering")
    sizes = np.array([index[name].size for name in names], dtype=np.int64)
    return FolderFiles(folder, names, sizes, FolderHashCache(folder, reset_cache=args.reset_cache))


def find_candidates(sizes_rows: np.ndarray, sizes_cols: np.ndarray, method: str) -> np.ndarray:
    """
    Decide from the sizes alone which files have to be compared at all.

    Returns:
        bool array (len(sizes_rows), len(sizes_cols)), true where a comparison is needed
    """
    if method not in MethodC.values():
        raise ValueError(f"Unknown method {method}, expected one of {MethodC.values()}")
    rows = np.expand_dims(sizes_rows, 1)
    cols = np.expand_dims(sizes_cols, 0)
    candidates = np.zeros((len(sizes_rows), len(sizes_cols)), dtype=bool)
    # in chunks, the full difference matrix of a big folder does not fit into memory
    for start in tqdm(range(0, len(sizes_rows), SIZE_COMPARE_CHUNK), desc="Comparing sizes"):
        end = min(start + SIZE_COMPARE_CHUNK, len(sizes_rows))
        if method == MethodC.EXACT:
            candidates[start:end] = np.equal(rows[start:end], cols)
            continue
        diffs = np.abs(rows[start:end] - cols)
        smaller = np.maximum(np.minimum(rows[start:end], cols), 1)
        candidates[start:end] = np.logical_or(
            diffs < APPROX_SIZE_DIFF_BYTES, diffs / smaller < APPROX_SIZE_DIFF_REL
        )
    return candidates


def find_duplicates(
    rows: FolderFiles,
    cols: FolderFiles,
    method: str = MethodC.EXACT,
    check_date_in_filename: bool = False,
) -> dict[str, list[str]]:
    """
    Compare the files of rows with the files of cols.

    Args:
        rows: the files duplicates are searched for
        cols: where they are searched. Pass the same object as rows to find the duplicates
            inside one folder, then no file is compared with itself and no pair twice.
        method: one of MethodC
        check_date_in_filename: files whose names hold different dates are never duplicates

    Returns:
        for each file of rows that has duplicates, their names in cols. Within one folder a
        file that was found as a duplicate is not listed again with duplicates of its own.
    """
    within = rows is cols
    candidates = find_candidates(rows.sizes, cols.sizes, method)
    if within:
        # no comparison with itself and none twice: drop the diagonal and the lower half
        candidates[np.tril_indices(len(rows.names))] = False
    logger.info(f"Total comparisons: {np.sum(candidates)}")

    pdf_texts: dict[Path, str] = {}
    duplicates = {}
    pbar = tqdm_max_ncols(total=len(rows.names), desc="Finding dups.")
    for i, name in enumerate(rows.names):
        pbar.update()
        candidate_row = candidates[i]
        if not np.any(candidate_row):
            continue
        logger.debug(f"Checking {name}")
        # mtime and name are unreliable, so the hashes and then the content decide
        found = []
        for j in np.argwhere(candidate_row).squeeze(-1):
            other = cols.names[j]
            if check_date_in_filename and dates_differ(name, other):
                logger.debug(f"Skipping {name} and {other}, their names hold different dates")
                continue
            if not files_match(rows, name, cols, other, method, pdf_texts):
                continue
            found.append(other)
            if within:
                # it is a duplicate of this file, so it must not start a group of its own
                candidates[j] = False
        if len(found) == 0:
            continue
        pbar.write(f"FOUND {len(found):5d} {name}")
        for other in found:
            pbar.write(f"            {other}")
        duplicates[name] = found
    pbar.close()
    rows.hashes.write_new_hashes()
    if not within:
        cols.hashes.write_new_hashes()
    return duplicates


def find_date(name: str) -> str | None:
    for re_date in RE_DATES:
        match = re_date.match(name)
        if match is not None:
            return match.group(1)
    return None


def dates_differ(name_a: str, name_b: str) -> bool:
    """Whether both file names hold a date and the dates are not the same."""
    date_a, date_b = find_date(name_a), find_date(name_b)
    return date_a is not None and date_b is not None and date_a != date_b


def files_match(
    rows: FolderFiles,
    name: str,
    cols: FolderFiles,
    other: str,
    method: str,
    pdf_texts: dict[Path, str],
) -> bool:
    if rows.hashes.get_hash(name) == cols.hashes.get_hash(other):
        return True
    if method == MethodC.EXACT:
        return False
    file_a, file_b = rows.folder / name, cols.folder / other
    if file_a.suffix.lower() != ".pdf" or file_b.suffix.lower() != ".pdf":
        # only PDFs have an approximate comparison, everything else must match exactly
        return False
    text_a, text_b = get_pdf_text(file_a, pdf_texts), get_pdf_text(file_b, pdf_texts)
    # a scan has no text. Two different scans would compare as equal, so no text is no match
    return text_a != "" and text_a == text_b


def get_pdf_text(pdf_file: Path, pdf_texts: dict[Path, str]) -> str:
    """The text of the PDF with all whitespace collapsed, so the line breaks and the layout
    that pdftotext picks do not matter. The dict keeps the texts of the files seen already."""
    if pdf_file not in pdf_texts:
        result = subprocess.run(
            ["pdftotext", pdf_file.as_posix(), "-"], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdftotext failed for {pdf_file}: {result.stderr.strip()}")
        pdf_texts[pdf_file] = " ".join(result.stdout.split())
    return pdf_texts[pdf_file]


def delete_files(folder: Path, names: list[str], write: bool) -> None:
    """Delete the files for good, or only log them without write."""
    verb = "deleting" if write else "would delete"
    for name in names:
        logger.info(f"{verb} {folder / name}")
        if write:
            (folder / name).unlink()
