from dataclasses import dataclass
from types import MappingProxyType
from typing import Sequence, Mapping

from lms.common.field.lms_datatype import LMS_DataType
from lms.titleconfig.definitions.field import FieldDefinition

@dataclass(frozen=True)
class AttributeDefinition(FieldDefinition):
    """
    Class that represents an attribute definition in a project.
    """
    offset: int

    @classmethod
    def from_dict(cls, data: dict):
        name, description, offset  = data["name"], data.get("description", ""), data["offset"]
        datatype = LMS_DataType.from_string(data["datatype"])
        enum_members = data.get("enum_members", {})
        return cls(name, description, datatype, MappingProxyType(enum_members), offset)





