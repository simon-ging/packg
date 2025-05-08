import os
import json
import tempfile
import time
import pytest
from packg.iotools.jsoncacher import JSONCacher


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def cache_file(temp_dir):
    return os.path.join(temp_dir, "cache.json")


@pytest.fixture
def json_files(temp_dir):
    # Create test JSON files
    files = {
        "data1.json": {"id": 1, "value": "test1"},
        "subfolder/data2.json": {"id": 2, "value": "test2"},
        "subfolder/deep/data3.json": {"id": 3, "value": "test3"},
    }

    for rel_path, data in files.items():
        full_path = os.path.join(temp_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            json.dump(data, f)

    return files


def test_initialization(cache_file):
    cacher = JSONCacher(cache_file)
    assert cacher.cache == {}
    assert os.path.exists(cache_file)


def test_update_from_directory(temp_dir, cache_file, json_files):
    cacher = JSONCacher(cache_file)
    cacher.update_from_directory(temp_dir)

    # Check if all files were cached
    assert len(cacher.cache) == 3

    # Check if data was stored correctly
    assert cacher.get("data1") == json_files["data1.json"]
    assert cacher.get("subfolder/data2") == json_files["subfolder/data2.json"]
    assert cacher.get("subfolder/deep/data3") == json_files["subfolder/deep/data3.json"]


def test_update_only_modified(temp_dir, cache_file, json_files):
    cacher = JSONCacher(cache_file)
    cacher.update_from_directory(temp_dir)

    # Get initial cache state
    initial_cache = cacher.cache.copy()  # type: ignore

    # Update one file
    modified_data = {"id": 1, "value": "modified"}
    with open(os.path.join(temp_dir, "data1.json"), "w") as f:
        json.dump(modified_data, f)

    # Wait a bit to ensure modification time changes
    time.sleep(0.1)

    # Update cache again
    cacher.update_from_directory(temp_dir)

    # Check if only modified file was updated
    assert cacher.get("data1") == modified_data
    assert cacher.get("subfolder/data2") == json_files["subfolder/data2.json"]
    assert cacher.get("subfolder/deep/data3") == json_files["subfolder/deep/data3.json"]


def test_get_all(temp_dir, cache_file, json_files):
    cacher = JSONCacher(cache_file)
    cacher.update_from_directory(temp_dir)

    all_data = cacher.items_dict()
    assert len(all_data) == 3
    assert all_data["data1"] == json_files["data1.json"]
    assert all_data["subfolder/data2"] == json_files["subfolder/data2.json"]
    assert all_data["subfolder/deep/data3"] == json_files["subfolder/deep/data3.json"]


def test_get_nonexistent(temp_dir, cache_file):
    cacher = JSONCacher(cache_file)
    cacher.update_from_directory(temp_dir)

    assert cacher.get("nonexistent") is None


def test_remove_deleted_files(temp_dir, cache_file, json_files):
    cacher = JSONCacher(cache_file)
    cacher.update_from_directory(temp_dir)

    # Delete a file
    os.remove(os.path.join(temp_dir, "data1.json"))

    # Update cache again
    cacher.update_from_directory(temp_dir)

    # Check if deleted file was removed from cache
    assert cacher.get("data1") is None
    assert len(cacher.cache) == 2
    assert cacher.get("subfolder/data2") == json_files["subfolder/data2.json"]
    assert cacher.get("subfolder/deep/data3") == json_files["subfolder/deep/data3.json"]
