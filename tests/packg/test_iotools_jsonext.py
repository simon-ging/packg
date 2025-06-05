import json
from pathlib import Path

import numpy as np
import pytest

from packg.iotools import (
    load_json,
    loads_json,
    load_jsonl,
    dump_json,
    dumps_json,
    dump_jsonl,
    dumps_jsonl,
    loads_jsonl,
    load_json_xz,
    dump_json_xz,
)
from packg.iotools.compress import load_xz, CompressorC
from packg.iotools.jsonext import (
    CustomJSONEncoder,
    dump_json_compressed,
    load_json_compressed,
    dump_jsonl_compressed,
    load_jsonl_compressed,
)
from typedparser.objects import modify_nested_object


# ---------- define input data for the tests


@pytest.fixture(scope="session")
def example_json_data_simplest():
    yield 7, "7"


@pytest.fixture(scope="session")
def example_json_data_regular():
    # no list, no numpy
    data_python = {
        "menü": {
            "id": "file",
            "popup": "lorem ipsum",
        }
    }
    data_json = """{
  "menü": {
    "id": "file",
    "popup": "lorem ipsum"
  }
}"""
    yield data_python, data_json


@pytest.fixture(scope="session")
def example_json_data_numpy_list():
    # with list, with numpy
    data_python = {
        "menü": {
            "ids": [
                6,
                np.int64(64),
                np.int8(8),
                np.int16(0),
                np.float16(16.0),
                np.float64(64.0),
                np.float32(0.0),
            ],
        }
    }
    data_json = """{
  "menü": {
    "ids": [6, 64, 8, 0, 16.0, 64.0, 0.0]
  }
}"""
    yield data_python, data_json


@pytest.fixture(scope="session")
def example_json_data_numpy_array():
    # with list, with numpy
    data_python = np.arange(6) + 0.5
    data_json = """[0.5, 1.5, 2.5, 3.5, 4.5, 5.5]"""
    yield data_python, data_json


@pytest.fixture(scope="session")
def example_json_data_path():
    # with path
    data_python = Path("/path/to/somewhere/test.json")
    data_json = '"/path/to/somewhere/test.json"'
    yield data_python, data_json


@pytest.fixture(
    scope="session",
    params=[
        example_json_data_simplest,
        example_json_data_regular,
        example_json_data_numpy_list,
        example_json_data_numpy_array,
        example_json_data_path,
    ],
    ids=("simplest", "regular", "np_scalar", "np_array", "path"),
)
def json_data_fixture(request):
    """Tests using this fixture will be run once for each of the input fixtures."""
    yield request.getfixturevalue(request.param.__name__)


# ---------- define the tests


def test_json_encoder(json_data_fixture):
    data_python, data_json = json_data_fixture
    data_json_encoded = json.dumps(data_python, cls=CustomJSONEncoder, indent=2, ensure_ascii=False)
    # make the comparison more readable by replacing spaces
    _compare_json_strings(data_json_encoded, data_json)


def test_json_dump_load(json_data_fixture, tmp_path):
    data_python, data_json = json_data_fixture
    tmp_file = tmp_path / "test.json"
    dump_json(data_python, tmp_file, indent=2)
    _compare_json_strings(tmp_file.read_text(encoding="utf8"), data_json)
    data_python_reloaded = load_json(tmp_file)
    _compare_objects(data_python, data_python_reloaded)


def test_json_xz_dump_load(json_data_fixture, tmp_path):
    data_python, data_json = json_data_fixture
    tmp_file = tmp_path / "test.json.xz"
    dump_json_xz(data_python, tmp_file, indent=2)
    data_decompr = load_xz(tmp_file)
    _compare_json_strings(data_decompr, data_json)
    data_python_reloaded = load_json_xz(tmp_file)
    _compare_objects(data_python, data_python_reloaded)


def test_json_dumps_loads(json_data_fixture):
    data_python, data_json = json_data_fixture
    _compare_json_strings(dumps_json(loads_json(data_json), indent=2), data_json)
    _compare_objects(loads_json(dumps_json(data_python, indent=2)), data_python)


# need new ground truth test data for jsonl, since it is a different format
_jsonl_data_python = [
    {"menü": {"id": "file", "popup": "lorem ipsum"}},
    {
        "menü": {
            "ids": [
                6,
                np.int64(64),
                np.int8(8),
                np.int16(0),
                np.float16(16.0),
                np.float64(64.0),
                np.float32(0.0),
            ]
        }
    },
    np.arange(6) + 0.5,
    Path("/path/to/somewhere/test.json"),
]
_jsonl_data_jsonl = (
    '{"menü":{"id":"file","popup":"lorem ipsum"}}\n'
    '{"menü":{"ids":[6,64,8,0,16.0,64.0,0.0]}}\n'
    "[0.5,1.5,2.5,3.5,4.5,5.5]\n"
    '"/path/to/somewhere/test.json"\n'
)


def test_jsonl_dump_load(tmp_path):
    tmp_file = tmp_path / "test.jsonl"
    dump_jsonl(_jsonl_data_python, tmp_file)
    _compare_json_strings(tmp_file.read_text(encoding="utf8"), _jsonl_data_jsonl)
    data_python_reloaded = load_jsonl(tmp_file)
    _compare_objects(_jsonl_data_python, data_python_reloaded)

    # also test the string mode
    data_json_created = dumps_jsonl(_jsonl_data_python)
    _compare_json_strings(data_json_created, _jsonl_data_jsonl)
    data_python_reloaded = loads_jsonl(data_json_created)
    _compare_objects(_jsonl_data_python, data_python_reloaded)


def test_json_dump_load_compressed(json_data_fixture, tmp_path):
    data_python, data_json = json_data_fixture
    for compressor_name in CompressorC.values():
        tmp_file = tmp_path / f"test.json_{compressor_name}"
        dump_json_compressed(data_python, tmp_file, compressor_name, indent=2)
        data_python_reloaded = load_json_compressed(tmp_file, compressor_name)
        _compare_objects(data_python, data_python_reloaded)


def test_jsonl_dump_load_compressed(tmp_path):
    for compressor_name in CompressorC.values():
        tmp_file = tmp_path / f"test.jsonl_{compressor_name}"
        dump_jsonl_compressed(_jsonl_data_python, tmp_file, compressor_name)
        data_python_reloaded = load_jsonl_compressed(tmp_file, compressor_name)
        _compare_objects(_jsonl_data_python, data_python_reloaded)


def test_dump_with_float_precision():
    num_inp = 0.010972334
    inp = {"mydata": num_inp}
    assert dumps_json(inp) == "{" f'"mydata":{num_inp}' "}"
    assert dumps_json(inp, float_precision=3) == "{" f'"mydata":{round(num_inp, 3)}' "}"
    assert dumps_json(inp, float_precision=0) == "{" f'"mydata":{round(num_inp)}' "}"


def test_dump_with_custom_format_indent_lists():
    """Test that custom_format_indent_lists controls whether lists are indented on new lines."""
    test_data = {"key1": [1, 2, 3], "key2": {"nested": [4, 5, 6]}}

    # With custom_format_indent_lists=True, lists should be indented
    expected_with_indent = """{
  "key1": [
    1,
    2,
    3
  ],
  "key2": {
    "nested": [
      4,
      5,
      6
    ]
  }
}"""
    assert dumps_json(test_data, indent=2, custom_format_indent_lists=True) == expected_with_indent

    # With custom_format_indent_lists=False, lists should be on the same line
    expected_without_indent = """{
  "key1": [1, 2, 3],
  "key2": {
    "nested": [4, 5, 6]
  }
}"""
    assert (
        dumps_json(test_data, indent=2, custom_format_indent_lists=False) == expected_without_indent
    )


def test_dump_nan_to_none_single_nan():
    """Test that a single NaN value is converted to null in JSON."""
    nan_data = {"mydata": float("nan")}
    assert dumps_json(nan_data, custom_format_nan_to_none=True) == '{"mydata":null}'


def test_dump_nan_to_none_regular_number():
    """Test that regular numbers are left unchanged."""
    regular_data = {"mydata": 1.0}
    assert dumps_json(regular_data, custom_format_nan_to_none=True) == '{"mydata":1.0}'


def test_dump_nan_to_none_mixed_data():
    """Test handling of mixed data with both NaN and regular numbers."""
    mixed_data = {"nan": float("nan"), "regular": 1.0}
    assert dumps_json(mixed_data, custom_format_nan_to_none=True) == '{"nan":null,"regular":1.0}'


def _compare_json_strings(candidate, reference):
    # make the comparison more readable by replacing spaces
    assert candidate.replace(" ", "~") == reference.replace(" ", "~")


def _compare_objects(obj_1, obj_2):
    """
    The json module does not do round trips, since it converts paths, arrays etc.
    Emulate that conversion also for the test ground truth data s.t. the test works.
    """

    def modifier_fn(obj):
        if isinstance(obj, Path):
            return obj.as_posix()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    obj_1 = modify_nested_object(obj_1, modifier_fn, return_copy=True)
    obj_2 = modify_nested_object(obj_2, modifier_fn, return_copy=True)
    assert obj_1 == obj_2
