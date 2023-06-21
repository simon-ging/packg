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
    class _C1(Const, allowed_types=str):
        FIELD = "value"


    with pytest.raises(TypeError):
        class _C2(Const, allowed_types=str):
            FIELD = 42


    class _C3(Const, allowed_types=(str, int)):
        FIELD = "value"
        FOO = 42


    with pytest.raises(TypeError):
        class _C4(Const, allowed_types=(str, float)):
            BAR = 42

    with pytest.raises(TypeError):
        class _C5(Const, allowed_types=str):
            BAR = True
