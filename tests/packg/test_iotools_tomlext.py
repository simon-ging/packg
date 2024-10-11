from pprint import pprint

from packg.iotools.tomlext import loads_toml

toml_string = """
[section]
key = "value"
number = 123
"""


def test_loads_toml():
    toml_dict = loads_toml(toml_string)
    assert toml_dict["section"]["key"] == "value"
    assert toml_dict["section"]["number"] == 123
    pprint(toml_dict)
