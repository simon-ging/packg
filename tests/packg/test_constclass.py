import pytest
from typing import List, Tuple
from packg.constclass import Const, InstanceToClassDelegator


def test_instance_to_class_delegator():
    class TestDelegator(metaclass=InstanceToClassDelegator):
        @classmethod
        def _class_str(cls):
            return "str_test"

        @classmethod
        def _class_repr(cls):
            return "repr_test"

        @classmethod
        def _class_iter(cls):
            return iter(["test"])

        @classmethod
        def _class_len(cls):
            return 42

        @classmethod
        def _class_instancecheck(cls):
            return True

    # Test str delegation
    assert str(TestDelegator) == "str_test"

    # Test repr delegation
    assert repr(TestDelegator) == "repr_test"

    # Test iter delegation
    assert list(TestDelegator) == ["test"]

    # Test len delegation
    assert len(TestDelegator) == 42

    # Test instancecheck delegation
    assert isinstance("test", TestDelegator)


def test_const_class_methods():
    class TestConst(Const):
        FIELD1 = "value1"
        FIELD2 = 42

    # Test _class_str and _class_repr
    assert TestConst._class_str() == str(TestConst)
    assert TestConst._class_repr() == repr(TestConst)

    # Test _class_len and _class_iter
    assert TestConst._class_len() == len(TestConst)
    assert list(TestConst._class_iter()) == list(TestConst)

    # Test _class_instancecheck
    assert TestConst._class_instancecheck("test") is True


def test_basic_const():
    class MyConstants(Const):
        FIELD1 = "value1"
        FIELD2 = 42

    # Test basic access
    assert MyConstants.FIELD1 == "value1"
    assert MyConstants.FIELD2 == 42

    # Test dict-like behavior
    assert len(MyConstants) == 2
    assert list(MyConstants.keys()) == ["FIELD1", "FIELD2"]
    assert list(MyConstants.values()) == ["value1", 42]
    assert list(MyConstants.items()) == [("FIELD1", "value1"), ("FIELD2", 42)]

    # Test get method
    assert MyConstants.get("FIELD1") == "value1"
    assert MyConstants.get("NONEXISTENT") is None
    assert MyConstants.get("NONEXISTENT", "default") == "default"

    # Test string representation
    str_repr = str(MyConstants)
    assert "FIELD1='value1'" in str_repr
    assert "FIELD2=42" in str_repr

    # Test instance prevention
    with pytest.raises(RuntimeError, match="Do not instance this class"):
        MyConstants()


def test_const_with_type_restrictions():
    class StringConstants(Const, allowed_types=str):
        FIELD1 = "value1"
        FIELD2 = "value2"

    # Test valid values
    assert StringConstants.FIELD1 == "value1"
    assert StringConstants.FIELD2 == "value2"

    # Test invalid value type
    with pytest.raises(TypeError, match="must be of type"):

        class InvalidStringConstants(Const, allowed_types=str):
            FIELD1 = "value1"
            FIELD2 = 42  # This should raise TypeError

    # Test multiple allowed types
    class MultiTypeConstants(Const, allowed_types=(str, int)):
        FIELD1 = "value1"
        FIELD2 = 42

    assert MultiTypeConstants.FIELD1 == "value1"
    assert MultiTypeConstants.FIELD2 == 42

    # Test list of allowed types
    class ListTypeConstants(Const, allowed_types=[str, int]):
        FIELD1 = "value1"
        FIELD2 = 42

    assert ListTypeConstants.FIELD1 == "value1"
    assert ListTypeConstants.FIELD2 == 42


def test_const_inheritance():
    class ParentConstants(Const):
        FIELD1 = "value1"
        FIELD2 = 42

    class ChildConstants(ParentConstants):
        FIELD3 = "value3"

    # Test inheritance of parent fields
    assert ChildConstants.FIELD1 == "value1"
    assert ChildConstants.FIELD2 == 42
    assert ChildConstants.FIELD3 == "value3"

    # Test that child has all fields
    assert len(ChildConstants) == 3
    assert set(ChildConstants.keys()) == {"FIELD1", "FIELD2", "FIELD3"}

    # Test that parent remains unchanged
    assert len(ParentConstants) == 2
    assert set(ParentConstants.keys()) == {"FIELD1", "FIELD2"}


def test_const_iteration():
    class IterConstants(Const):
        FIELD1 = "value1"
        FIELD2 = "value2"
        FIELD3 = "value3"

    # Test iteration over keys
    keys = list(IterConstants)
    assert keys == ["FIELD1", "FIELD2", "FIELD3"]

    # Test values_list and keys_list methods
    assert IterConstants.values_list() == ["value1", "value2", "value3"]
    assert IterConstants.keys_list() == ["FIELD1", "FIELD2", "FIELD3"]


def test_const_contains():
    class ContainsConstants(Const):
        FIELD1 = "value1"
        FIELD2 = "value2"

    assert "FIELD1" in ContainsConstants
    assert "FIELD2" in ContainsConstants
    assert "NONEXISTENT" not in ContainsConstants


def test_const_getitem():
    class GetItemConstants(Const):
        FIELD1 = "value1"
        FIELD2 = "value2"

    # Test class-level getitem
    assert GetItemConstants["FIELD1"] == "value1"
    assert GetItemConstants["FIELD2"] == "value2"

    # Test instance getitem prevention
    with pytest.raises(RuntimeError, match="Do not instance this class"):
        GetItemConstants()["FIELD1"]

    # Test non-existent key
    with pytest.raises(KeyError, match="NONEXISTENT in"):
        GetItemConstants["NONEXISTENT"]


def test_const_with_private_fields():
    class PrivateConstants(Const):
        FIELD1 = "value1"
        _PRIVATE_FIELD = "private"
        FIELD2 = "value2"

    # Test that private fields are not included
    assert len(PrivateConstants) == 2
    assert set(PrivateConstants.keys()) == {"FIELD1", "FIELD2"}
    assert "FIELD1" in PrivateConstants
    assert "_PRIVATE_FIELD" not in PrivateConstants


def test_const_with_methods():
    class MethodConstants(Const):
        FIELD1 = "value1"

        @classmethod
        def my_method(cls):
            return "method"

    # Test that methods are not included in the constants
    assert len(MethodConstants) == 1
    assert set(MethodConstants.keys()) == {"FIELD1"}
    assert MethodConstants.my_method() == "method"


def test_const_multiple_inheritance():
    class MixinClass:
        def mixin_method(self):
            return "mixin"

    class MultiInheritConstants(MixinClass, Const):
        FIELD1 = "value1"

    # Test that non-Const parent classes are handled correctly
    assert len(MultiInheritConstants) == 1
    assert set(MultiInheritConstants.keys()) == {"FIELD1"}


def test_const_repr():
    class ReprConstants(Const):
        FIELD1 = "value1"
        FIELD2 = 42

    # Test repr output
    repr_str = repr(ReprConstants)
    assert "ReprConstants" in repr_str
    assert "FIELD1='value1'" in repr_str
    assert "FIELD2=42" in repr_str
