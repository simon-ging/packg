import inspect
from abc import ABCMeta, abstractmethod
from typing import (
    Iterator,
    Optional,
    List,
    ItemsView,
    KeysView,
    ValuesView,
    Any,
    Dict,
    Tuple,
    Union,
)


class InstanceToClassDelegator(ABCMeta):
    """Metaclass to delegate instance methods to class methods, e.g.:
    __str__(MyClass) will call MyClass._class_str()."""

    def __str__(cls):
        return cls._class_str()  # noqa  # pylint: disable=no-value-for-parameter

    def __repr__(cls):
        return cls._class_repr()  # noqa  # pylint: disable=no-value-for-parameter

    def __iter__(cls):
        return cls._class_iter()  # noqa  # pylint: disable=no-value-for-parameter

    def __len__(cls):
        return cls._class_len()  # noqa  # pylint: disable=no-value-for-parameter

    def __instancecheck__(cls, instance):
        return cls._class_instancecheck()  # noqa  # pylint: disable=no-value-for-parameter

    @abstractmethod
    def _class_str(cls):
        pass

    @abstractmethod
    def _class_repr(cls):
        pass

    @abstractmethod
    def _class_iter(cls):
        pass

    @abstractmethod
    def _class_len(cls):
        pass

    @abstractmethod
    def _class_instancecheck(cls):
        pass


class Const(metaclass=InstanceToClassDelegator):
    """
    Class to hold constants. Cannot be instanced. Behaves similar to a dict.
    This is an approach to overcome some weaknesses of enum.Enum
    (e.g. having to use MyEnum.field.value to get the value).

    Examples:
        Simplest example:
        >>> class MyConstants(Const):
        >>>     FIELD = "value"
        >>> print(MyConstants.FIELD)
        value

        Restrict the types of the constants to one or more types, raising errors on mismatch:
        >>> class MyOtherConstants(MyConstants, allowed_types=str):
        >>>     OTHER_FIELD = "other_value"
        >>> class MoreConstants(Const, allowed_types=(str, int)):
        >>>     OTHER_FIELD = "other_value"
        >>>     OTHER_FIELD_2 = 2

    """

    # create the class properties with empty entries for the root parent
    _dict: Dict[str, Dict[str, Any]] = {"Const": {}}

    @classmethod
    def _get_dict(cls):
        return cls._dict[cls.__name__]

    @classmethod
    def keys(cls) -> KeysView[str]:
        return cls._get_dict().keys()

    @classmethod
    def values(cls) -> ValuesView[Any]:
        return cls._get_dict().values()

    @classmethod
    def items(cls) -> ItemsView[str, Any]:
        return cls._get_dict().items()

    @classmethod
    def get(cls, item: str, default: Any = None) -> Any:
        try:
            val = cls[item]
        except KeyError:
            return default
        return val

    @classmethod
    def __class_getitem__(cls, item: str):
        try:
            val = cls._get_dict()[item]
        except AttributeError as e:
            raise KeyError(f"{item} in {cls}") from e
        return val

    def __getitem__(self, item: str):
        raise RuntimeError("Const subclass cannot be instanced")

    @classmethod
    def __len__(cls) -> int:
        return len(cls.keys())

    @classmethod
    def __iter__(cls) -> Iterator[Any]:
        return iter(cls.keys())

    @classmethod
    def __contains__(cls, item: str) -> bool:
        return item in cls.keys()

    @classmethod
    def _class_str(cls) -> str:
        return f"{cls.__name__}({', '.join('='.join((k, repr(v))) for k, v in cls.items())})"

    @classmethod
    def _class_repr(cls) -> str:
        return cls._class_str()

    @classmethod
    def _class_len(cls):
        return len(cls.keys())

    @classmethod
    def _class_iter(cls):
        return iter(cls.keys())

    @classmethod
    def _class_instancecheck(cls, instance):
        return isinstance(instance, str)

    @classmethod
    def __init_subclass__(
        cls, allowed_types: Optional[Union[type, List[type], Tuple[type, ...]]] = None
    ) -> None:
        """
        Setup properties for the public interface when this class is inherited.

        This will be called on nested inheritance as well.

        Args:
            allowed_types: Optionally specify a type or list of types that are allowed for values.
                By default all values are allowed.
        """
        cls._dict[cls.__name__] = {}

        # add parent fields
        for parent_cls in cls.__bases__:
            try:
                cls._dict[cls.__name__].update(cls._dict[parent_cls.__name__])
            except KeyError:
                # ignore errors when parent class is not a ConstantHolder, eg multiple inheritance
                pass

        # loop attributes, check correctness and extend the parent's class properties _keys, _values, _dict.
        for key in cls.__dict__.keys():
            # ignore non-public fields
            if key[0] == "_":
                continue

            # get the value of the constant
            value = getattr(cls, key)

            # ignore classmethods
            if inspect.ismethod(value) and value.__self__ is cls:
                continue

            # if allowed types is specified, make sure the value types are allowed
            if allowed_types is not None:
                # isinstance errors when fed lists instead of tuple, so convert lists to tuples
                if isinstance(allowed_types, list):
                    allowed_types = tuple(allowed_types)
                if not isinstance(value, allowed_types):
                    raise TypeError(
                        f"Constant: {key} in class: {cls.__name__} must be of type {allowed_types}"
                    )

            # update class properties
            cls._dict[cls.__name__][key] = value

    def __init__(self) -> None:
        raise RuntimeError(f"Do not instance this class, it's a Const: {type(self).__name__}")
