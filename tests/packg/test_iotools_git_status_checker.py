from packg.iotools.git_status_checker import (
    get_gitadd_dryrun_output,
    parse_gitadd_dryrun_output,
)
from packg.testing.setup_tests import git_example_fixture, session_tmp_path

_ = git_example_fixture, session_tmp_path  # remove the unused false positive


def test_gitadd_dryrun_lines(git_example_fixture):
    out_str = get_gitadd_dryrun_output(git_example_fixture)
    files_and_status = parse_gitadd_dryrun_output(out_str, git_example_fixture)
    assert files_and_status == {"a": "add", "b": "remove", "e": "add"}, files_and_status
