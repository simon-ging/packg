from packg.paths import get_packg_data_dir, get_packg_cache_dir


def test_paths():
    # todo test setting env vars with pytest
    # todo set overwrite_dir param and check results
    print(f"data_dir={get_packg_data_dir()}")
    print(f"cache_dir={get_packg_cache_dir()}")
    assert True
