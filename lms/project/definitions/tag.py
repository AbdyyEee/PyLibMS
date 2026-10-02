from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from lms.common.field.lms_datatype import LMS_DataType


class LMS_TagGroup:
    """
    Represents a tag group, container for definition of tags.

    https://nintendo-formats.com/libs/lms/msbp.html#tag-group
    """

    def __init__(
            self,
            name: str,
            group_id: int,
            tag_indexes: list[int],
    ):
        self._name = name
        self._id = group_id
        self._tag_indices = tag_indexes

        self._tag_definitions: list[LMS_TagDefinition] = []

    @property
    def name(self) -> str:
        """Name of the tag group."""
        return self._name

    @property
    def group_id(self) -> int:
        """ID of the tag group."""
        return self._id

    @property
    def tag_definitions(self):
        """Tag definitions owned by this group."""
        return tuple(self._tag_definitions)

    def set_all_definitions(
            self,
            tag_definitions: list[LMS_TagDefinition],
            param_definitions: list[LMS_TagParamDefinition],
            tag_enums: list[str] = None,
    ) -> None:

        self._tag_definitions.extend(tag_definitions[i] for i in self._tag_indices)
        for tag in self._tag_definitions:
            tag.set_parameter_definitions(param_definitions)

            for parameter in tag.parameter_definitions:
                if parameter.datatype is not LMS_DataType.ENUM:
                    continue

                parameter.set_enum_members(tag_enums)


class LMS_TagDefinition:
    """
    Represents a singular tag definition.

    https://nintendo-formats.com/libs/lms/msbp.html#tag
    """

    def __init__(
            self,
            name: str,
            parameter_indices: list[int],
    ):
        self._name = name
        self._parameter_indices = (
            parameter_indices if parameter_indices is not None else []
        )
        self._parameter_definitions: list[str] = None

    @property
    def name(self) -> str:
        """Name of the tag."""
        return self._name

    @property
    def parameter_definitions(self) -> tuple[LMS_TagParamDefinition, ...]:
        """Parameter definitions of the tag."""
        return tuple(self._parameter_definitions)

    @property
    def parameter_indices(self) -> list[int]:
        return self._parameter_indices

    def set_parameter_definitions(self, definitions: list[LMS_TagParamDefinition]) -> None:
        self._parameter_definitions = [definitions[i] for i in self._parameter_indices]


class LMS_TagParamDefinition:
    """
    Represents a singular tag parameter definition.

    https://nintendo-formats.com/libs/lms/msbp.html#tag-parameter
    """

    def __init__(
            self,
            name: str,
            datatype: LMS_DataType,
            enum_indices: list[int] | None = None,
    ):
        self._name = name
        self._enum_members: MappingProxyType[int, str] = None

        self._datatype = datatype
        self._enum_indices = enum_indices if enum_indices is not None else []

    @property
    def name(self) -> str:
        """Name of the parameter."""
        return self._name

    @property
    def datatype(self) -> LMS_DataType:
        """Datatype of the parameter."""
        return self._datatype

    @property
    def enum_members(self) -> Mapping[int, str]:
        """Mapping of enum members."""
        return self._enum_members

    @property
    def enum_indices(self) -> list[int]:
        return self._enum_indices

    def set_enum_members(self, tag_enums: list[str]) -> None:
        enum_members = tag_enums[self.enum_indices[0]:self.enum_indices[-1] + 1]
        self._enum_members = MappingProxyType({i: enum for i, enum in enumerate(enum_members)})
