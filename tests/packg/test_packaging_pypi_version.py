from packg import packaging
from packg.packaging import find_pypi_package_version

_RESPONSE_TO_TEST = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="86" height="20" role="img" aria-label="pypi: v1.26.1"><title>pypi: v1.26.1</title><linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><clipPath id="r"><rect width="86" height="20" rx="3" fill="#fff"/></clipPath><g clip-path="url(#r)"><rect width="33" height="20" fill="#555"/><rect x="33" width="53" height="20" fill="#007ec6"/><rect width="86" height="20" fill="url(#s)"/></g><g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110"><text aria-hidden="true" x="175" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="230">pypi</text><text x="175" y="140" transform="scale(.1)" fill="#fff" textLength="230">pypi</text><text aria-hidden="true" x="585" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="430">v1.26.1</text><text x="585" y="140" transform="scale(.1)" fill="#fff" textLength="430">v1.26.1</text></g></svg>'


def test_find_pypi_package_version(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(packaging, "_get_raw_shields_io_output", lambda *a, **kw: _RESPONSE_TO_TEST)
        query_version = find_pypi_package_version("numpy")
        assert query_version == "1.26.1", f"query_version={query_version} != 1.26.1"
