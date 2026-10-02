from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from lms.common.field.lms_datatype import LMS_DataType


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    description: str
    datatype: LMS_DataType
    enum_members: Mapping[int, str]

    @classmethod
    def from_dict(cls, data: dict):
        name, description = data["name"], data.get("description", "")
        datatype = LMS_DataType.from_string(data["datatype"])

        enum_members = data.get("enum_members")

        if enum_members is not None:
            return cls(name, description, datatype, MappingProxyType(enum_members))

        # Fallback for LIST type
        list_items = data.get("list_items", {})

        members = {}
        for i, item in enumerate(list_items):
            members[i] = item

        return cls(name, description, datatype, MappingProxyType(members))
