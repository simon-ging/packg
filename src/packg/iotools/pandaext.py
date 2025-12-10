"""
pandas with more sensible defaults
"""
from pathlib import Path
from timeit import default_timer
import pandas as pd

from packg.iotools.jsonext import load_json


def load_parquet(file, dtype_backend="pyarrow", verbose: bool = False, **kwargs):
    file = Path(file)
    if verbose:
        start_timer = default_timer()
        file_len = f"{file.stat().st_size / 1024 ** 2:.1f} MB"
        print(f"Load json file {file} with size {file_len}.")
    data = pd.read_parquet(file, dtype_backend=dtype_backend, **kwargs)
    if verbose:
        print(f"Loaded json file {file} in {default_timer() - start_timer:.3f} seconds")
    return data


def dump_parquet(df, file, engine="pyarrow", compression="snappy", **kwargs):
    df.to_parquet(file, engine=engine, compression=compression, **kwargs)

def load_json_to_df(file):
    """Load JSON file into a pandas DataFrame.

    Args:
        file: Path to JSON file. The file must be a dict like {index1: {column1_key: column1_value, ...}, ...}

    Returns:
        pd.DataFrame: DataFrame created from JSON data
    """
    dct = load_json(file)
    df = pd.DataFrame.from_dict(dct, orient="index")
    return df
