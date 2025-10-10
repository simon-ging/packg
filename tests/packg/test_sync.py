from pathlib import Path

import pytest

from packg.cli.keep_remote_synced import SyncCollector
from packg.testing.setup_tests import git_example_fixture, session_tmp_path


_ = session_tmp_path  # stops it from being unused, it is used in the other fixture and required.


def test_sync_collector(git_example_fixture):
    # collect files in git_dir relative to git_dirs parent
    base_dir = Path(git_example_fixture).parent
    sync = SyncCollector(base_dir)
    with pytest.raises(AssertionError):
        # should crash due to staged dirs
        sync.collect_from_local_dir(git_example_fixture)
    files = sync.get_all_collected_files()
    assert set(files) == set([f"git_example/{f}" for f in ["a", "e", "c2", "f", "g"]])
