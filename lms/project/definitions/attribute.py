from types import MappingProxyType
from typing import Mapping

from lms.common.field.lms_datatype import LMS_DataType


class LMS_AttributeDefinition:
    def __init__(self, datatype: LMS_DataType, offset: int, enum_index: int):
        self.name: str | None = None

        self._enum_members: MappingProxyType[int, str] = None
        self._datatype = datatype
        self._offset = offset
        self._enum_index = enum_index

    @property
    def datatype(self) -> LMS_DataType:
        """Datatype of the attribute"""
        return self._datatype

    @property
    def offset(self) -> int:
        """Relative offset of the attribute in an ATR1 container."""
        return self._offset

    @property
    def enum_members(self) -> Mapping[int, str]:
        """Enum members of the attribute."""
        return self._enum_members

    def set_enum_members(self, attr_enums: list[Mapping[int, str]]) -> None:
        self._enum_members = attr_enums[self._enum_index]
