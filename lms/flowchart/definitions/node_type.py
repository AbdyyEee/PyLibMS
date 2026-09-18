from enum import IntEnum
from typing import Type

from lms.common.field.lms_datatype import LMS_DataType

PARAMETER_ALIASES = {
    "p32_0": "PARAM_32_0",
    "p16_16": "PARAM_16_16",
    "p16_8_8": "PARAM_16_8_8",
    "p8_8_16": "PARAM_8_8_16",
    "p8_8_8_8": "PARAM_8_8_8_8",
    "str": "STRING",
    "p32_1": "PARAM_32_1",
}


class LMS_NodeType(IntEnum):
    """
    Enum that defines node type.

    See https://nintendo-formats.com/libs/lms/msbf.html#node-types for more information.
    """

    MESSAGE = 1
    BRANCH = 2
    EVENT = 3
    ENTRY = 4
    JUMP = 5

    @classmethod
    def from_string(cls, string: str):
        """Creates an enum value from its string representation"""
        member = string.upper()
        if member in cls.__members__:
            return cls[member]
        else:
            raise ValueError(f"Unknown value of '{string}' was provided!")


class LMS_NodeParameterType(IntEnum):
    """
    Enum that defines the parameter type of node.

    See https://nintendo-formats.com/libs/lms/msbf.html#parameter-types for more information.
    """

    PARAM_32_0 = 0
    PARAM_16_16 = 1
    PARAM_16_8_8 = 2
    PARAM_8_8_16 = 3
    PARAM_8_8_8_8 = 4
    STRING = 5
    PARAM_32_1 = 6
    NONE = -1

    @property
    def sliced_datatype(self) -> tuple[LMS_DataType, ...]:
        """The parameter type split into the raw datatypes. Not valid for STRING."""
        if self in [
            LMS_NodeParameterType.NONE,
            LMS_NodeParameterType.STRING]:
            raise TypeError(f"There is no sliced datatypes for {self} parameter types!")

        return {
            LMS_NodeParameterType.PARAM_32_0: (LMS_DataType.UINT32,),
            LMS_NodeParameterType.PARAM_16_16: (LMS_DataType.UINT16, LMS_DataType.UINT16),
            LMS_NodeParameterType.PARAM_16_8_8: (LMS_DataType.UINT16, LMS_DataType.UINT8, LMS_DataType.UINT8),
            LMS_NodeParameterType.PARAM_8_8_16: (LMS_DataType.UINT8, LMS_DataType.UINT8, LMS_DataType.UINT16),
            LMS_NodeParameterType.PARAM_8_8_8_8: (LMS_DataType.UINT8, LMS_DataType.UINT8, LMS_DataType.UINT8,
                                                  LMS_DataType.UINT8),
            LMS_NodeParameterType.PARAM_32_1: (LMS_DataType.UINT32,)
        }[self]

    @property
    def value_count(self) -> int:
        """Amount of values the parameter holds."""
        if self is LMS_NodeParameterType.NONE:
            raise TypeError("There is no value count for NONE parameter types!")

        return {
            LMS_NodeParameterType.PARAM_32_0: 1,
            LMS_NodeParameterType.PARAM_16_16: 2,
            LMS_NodeParameterType.PARAM_8_8_16: 3,
            LMS_NodeParameterType.PARAM_16_8_8: 3,
            LMS_NodeParameterType.PARAM_8_8_8_8: 4,
            LMS_NodeParameterType.STRING: 1,
            LMS_NodeParameterType.PARAM_32_1: 1,
        }[self]

    @property
    def builtin_type(self) -> Type[int] | Type[tuple[int, ...]] | Type[str]:
        """The builtin type of the parameter type."""
        if self is LMS_NodeParameterType.NONE:
            raise TypeError("There is no builtin type for NONE parameter types!")

        return {
            LMS_NodeParameterType.PARAM_32_0: int,
            LMS_NodeParameterType.PARAM_16_16: tuple,
            LMS_NodeParameterType.PARAM_8_8_16: tuple,
            LMS_NodeParameterType.PARAM_16_8_8: tuple,
            LMS_NodeParameterType.PARAM_8_8_8_8: tuple,
            LMS_NodeParameterType.STRING: str,
            LMS_NodeParameterType.PARAM_32_1: int,
        }[self]

    @classmethod
    def from_string(cls, string: str):
        """Creates an enum value from its string representation"""
        member = string.upper()
        if member in cls.__members__:
            return cls[member]

        alias_member = PARAMETER_ALIASES.get(string.lower())
        if alias_member is not None:
            return cls[alias_member]
        else:
            raise ValueError(f"Unknown value of '{string}' was provided!")
