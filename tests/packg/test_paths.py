from packg.paths import (
    get_data_dir,
    get_result_dir,
    get_anno_dir,
    get_code_dir,
    get_cache_dir,
)


def test_paths():
    # todo test setting env vars with pytest
    # todo set overwrite_dir param and check results
    print(f"data_dir={get_data_dir()}")
    print(f"result_dir={get_result_dir()}")
    print(f"anno_dir={get_anno_dir()}")
    print(f"code_dir={get_code_dir()}")
    print(f"cache_dir={get_cache_dir()}")
    assert True
