import pytest

from packg.constclass import Const


class MyConstants(Const):
    FIELD = "value"


def test_const_class():
    assert MyConstants.FIELD == "value"
    assert "FIELD" in MyConstants.keys()
    assert MyConstants.get("FIELD") == "value"
    with pytest.raises(RuntimeError):
        MyConstants()
