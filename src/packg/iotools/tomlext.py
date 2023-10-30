import logging
from timeit import default_timer as timer

import tomlkit
from tomlkit import TOMLDocument

from packg.iotools.file_reader import read_text_from_file_or_io
from packg.typext import PathOrIO


def load_toml(file_or_io: PathOrIO, verbosity: int = logging.WARNING) -> TOMLDocument:
    start_timer = timer()
    data_str = read_text_from_file_or_io(file_or_io)
    try:
        data_toml = loads_toml(data_str)
    except Exception as e:
        print(f"Error loading toml file {file_or_io}: {e}")
        raise e
    if verbosity <= logging.INFO:
        print(f"Loaded json file {file_or_io} in {timer() - start_timer:.3f} seconds")
    return data_toml


def loads_toml(s: str) -> TOMLDocument:
    source_toml_dict: TOMLDocument = tomlkit.loads(s)
    return source_toml_dict


# source_toml_str_re = tomlkit.dumps(source_toml_dict)


# # todo
# def dump_toml():
#     raise NotImplementedError()
#
#
# def dumps_toml():
#     raise NotImplementedError()
