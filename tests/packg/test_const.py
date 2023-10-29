import attr
import pytest

from packg.constclass import Const


def test_const():
    class TestConst(Const):
        FIELD = "value"

    assert TestConst.FIELD == "value"
    assert dict(TestConst) == {"FIELD": "value"}
    assert list(TestConst) == ["FIELD"]
    assert len(TestConst) == 1
    assert list(TestConst.keys()) == ["FIELD"]
    assert list(TestConst.values()) == ["value"]
    assert list(TestConst.items()) == [("FIELD", "value")]
    assert "FIELD" in TestConst
    assert TestConst.get("FIELD") == "value"
    assert TestConst.get("FIELD2") is None
    assert TestConst.get("FIELD2", "default") == "default"
    assert TestConst["FIELD"] == "value"

    # test if class getitem breaks the typing
    as_ann: TestConst[str] = 7
    print(as_ann)


def test_const_allowed_types():
    class _C1(Const, allowed_types=str):  # noqa
        FIELD = "value"

    with pytest.raises(TypeError):

        class _C2(Const, allowed_types=str):  # noqa
            FIELD = 42

    class _C3(Const, allowed_types=(str, int)):  # noqa
        FIELD = "value"
        FOO = 42

    with pytest.raises(TypeError):

        class _C4(Const, allowed_types=(str, float)):  # noqa
            BAR = 42

    with pytest.raises(TypeError):

        class _C5(Const, allowed_types=str):  # noqa
            BAR = True


class MyConst(Const, allowed_types=(str, int)):
    C_STR = "text"
    C_INT = 4


@attr.s(auto_attribs=True, frozen=True)
class MyAttrConst:
    """This is another option to create constants"""

    C_STR = "text"
    C_INT = 4


def test_constantholder():
    assert MyConst.C_STR == "text"
    assert MyConst.C_INT == 4
    assert MyConst.get("C_STR") == "text"
    assert MyConst.get("missing_key") is None
    assert MyConst.get("missing_key", 7) == 7
    assert "C_STR" in MyConst
    assert "missing_key" not in MyConst
    assert list(MyConst) == ["C_STR", "C_INT"]
    ref_dict = {"C_STR": "text", "C_INT": 4}
    assert dict(MyConst) == ref_dict
    assert list(MyConst.keys()) == list(ref_dict.keys())
    assert list(MyConst.values()) == list(ref_dict.values())
    assert list(MyConst.items()) == list(ref_dict.items())
    assert len(MyConst) == 2
    assert list(MyConst) == ["C_STR", "C_INT"]
    assert str(MyConst) == "MyConst(C_STR='text', C_INT=4)"
    assert repr(MyConst) == str(MyConst)
