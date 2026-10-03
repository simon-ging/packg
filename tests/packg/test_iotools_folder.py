from pathlib import Path

from packg.iotools.folder import Folder, get_subfolder_data, print_graph
from packg.testing.setup_tests import git_example_fixture, session_tmp_path

_fixtures = [session_tmp_path, git_example_fixture]  # disable removing as unused imports


def test_folder_class(git_example_fixture):
    print(f"path: {Path(git_example_fixture)}")
    folder = Folder(git_example_fixture)
    folder.populate(recursive=True)
    print(f"\ndir_index: {folder.get_dir_index()}")
    rows = get_subfolder_data(folder, min_size_mb=0)
    print(f"rows: {rows}")
    assert len(rows) > 0
    paths = [path for path, _kind, _size, _mtime in rows]
    kinds = {kind for _path, kind, _size, _mtime in rows}
    assert kinds == {"f", "d"}, kinds
    # the root folder itself is the last row and holds everything below it
    assert rows[-1][2] == folder.total_size > 0
    assert len(set(paths)) == len(paths)

    lines = []
    print_graph(folder, min_size_mb=0, print_fn=lines.append)
    # the same entries as the table, files marked F and folders D. Empty folders are left out.
    assert len(lines) == len([size for _path, _kind, size, _mtime in rows[:-1] if size > 0]) + 1
    assert lines[-1].split()[1] == "D"
    assert any(line.split()[1] == "F" and line.endswith("a ") for line in lines)
