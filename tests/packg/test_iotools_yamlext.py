import pytest

from packg.iotools.yamlext import dump_yaml, dumps_yaml, load_yaml, loads_yaml

_python_obj = {
    "sub": {"str_val": "value"},
    "int_vals": [1, 2],
    "float_val": 1.3,
    "bool_val": True,
    "none_val": None,
    "param_overrides": [
        [["^scratch."], {"lr_mult": 10}],
        [["^frozen."], [["lr_mult", 1e-11]]],
    ],
}
_yaml_str_nonstandard = """sub:
    str_val: "value"
int_vals: [1, 2]
float_val: 1.3
bool_val: true
none_val: null
param_overrides: [[["^scratch."], {lr_mult: 10}], [["^frozen."], [["lr_mult", 1.0e-11]]]]"""
_yaml_str_standard = """bool_val: true
float_val: 1.3
int_vals:
- 1
- 2
none_val: null
param_overrides:
- - - ^scratch.
  - lr_mult: 10
- - - ^frozen.
  - - - lr_mult
      - 1.0e-11
sub:
  str_val: value"""


# test parameters: input object, ref string (custom format), optional ref string (standard format)
@pytest.fixture(
    params=[
        pytest.param((_python_obj, _yaml_str_nonstandard, _yaml_str_standard), id="nested"),
        pytest.param(({"a1": "value"}, 'a1: "value"', "a1: value"), id="flat"),
        pytest.param((1e-7, "1.0e-07\n...", None), id="scientific_float_1"),
        pytest.param((1e-1, "0.1\n...", None), id="scientific_float_2"),
    ]
)
def input_object_fixture(request):
    input_dict, ref_nonstandard, ref_standard = request.param
    if ref_standard is None:
        ref_standard = ref_nonstandard
    yield input_dict, ref_nonstandard, ref_standard


def test_yaml_dumps_loads(input_object_fixture):
    input_dict, ref_str_nonstandard, ref_str_standard = input_object_fixture

    # check if references equal the input object
    assert loads_yaml(ref_str_nonstandard) == input_dict
    assert loads_yaml(ref_str_standard) == input_dict

    # test roundtrip for nonstandard format
    cand_str_nonstandard = dumps_yaml(input_dict, standard_format=False)
    assert cand_str_nonstandard.strip() == ref_str_nonstandard.strip()
    assert loads_yaml(cand_str_nonstandard) == input_dict

    # test roundtrip for standard format (yaml.dump)
    cand_str_standard = dumps_yaml(input_dict, standard_format=True)
    assert cand_str_standard.strip() == ref_str_standard.strip()
    assert loads_yaml(cand_str_standard) == input_dict


def test_yaml_dump_load(input_object_fixture, tmp_path):
    input_dict, ref_str_nonstandard, ref_str_standard = input_object_fixture

    # test roundtrip for nonstandard format
    file = tmp_path / "test_nonstandard.yaml"
    dump_yaml(input_dict, file, standard_format=False)
    assert file.read_text(encoding="utf-8").strip() == ref_str_nonstandard.strip()
    assert load_yaml(file) == input_dict

    # test roundtrip for standard format (yaml.dump)
    file = tmp_path / "test_standard.yaml"
    dump_yaml(input_dict, file, standard_format=True)
    assert file.read_text(encoding="utf-8").strip() == ref_str_standard.strip()
    assert load_yaml(file) == input_dict


def test_yamls_roundtrip_with_empty_dict():
    input_dict = {"empty": {}}
    ref_str_nonstandard = "empty: {}\n"
    ref_str_standard = "empty: {}\n"

    # test roundtrip for standard format (yaml.dump)
    cand_str_standard = dumps_yaml(input_dict, standard_format=True)
    assert cand_str_standard.strip() == ref_str_standard.strip()
    assert loads_yaml(cand_str_standard) == input_dict

    # test roundtrip for nonstandard format
    cand_str_nonstandard = dumps_yaml(input_dict, standard_format=False)
    assert cand_str_nonstandard.strip() == ref_str_nonstandard.strip()
    assert loads_yaml(cand_str_nonstandard) == input_dict
