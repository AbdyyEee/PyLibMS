from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, overload

from lms.project.definitions.tag import LMS_TagDefinition
from lms.titleconfig.definitions.field import FieldDefinition


class TagConfig:
    """Class that represents a tag structure definition."""

    def __init__(self, group_map: dict[int, str]):
        self._group_map = MappingProxyType(group_map)
        self._definition_id_map = {}
        self._definition_name_map = {}

    @overload
    def __getitem__(self, group: int) -> tuple[LMS_TagDefinition, ...]:
        ...

    @overload
    def __getitem__(self, group: str) -> Mapping[str, LMS_TagDefinition]:
        ...

    def __getitem__(self, group: int | str) -> tuple[LMS_TagDefinition, ...] | Mapping[str, LMS_TagDefinition]:
        return self._definition_id_map.get(group) if isinstance(group, int) else self._definition_name_map.get(group)

    @property
    def group_map(self) -> Mapping[int, str]:
        """Maps of groups tied to the configuration."""
        return self._group_map

    @property
    def definitions(self) -> Mapping[int, list[TagDefinition]]:
        """Definitions for the tag configuration."""
        return MappingProxyType(self._definitions)

    def add_definition(self, definition: TagDefinition) -> None:
        """
        Adds a tag definition to the configuration.

        :param definition: The tag definition.
        """
        self._definition_id_map.setdefault(definition.group_id, []).append(definition)
        self._definition_name_map.setdefault(definition.group_name, {})[definition.tag_name] = definition

    def definitions_under_group(self, group: int) -> tuple[TagDefinition, ...]:
        definitions = []
        for definition in self._definitions:
            if definition.group_id == group:
                definitions.append(definition)
        return tuple(definitions)


@dataclass(frozen=True)
class TagDefinition:
    """Class that represents a single definition in the tag config."""

    group_name: str
    group_id: int
    tag_name: str
    tag_index: int
    description: str
    parameters: tuple[FieldDefinition, ...]

    @classmethod
    def from_dict(cls, data: dict, group_map: dict[int, str]):
        tag_name = data["name"]
        group_id, tag_index = data["group_id"], data["tag_index"]
        description = data.get("description", "")
        group_name = group_map[group_id]
        parameters = data.get("parameters", ())

        if not parameters:
            return cls(group_name, group_id, tag_name, tag_index, description, parameters)

        parameters = []
        for param_def in data["parameters"]:
            parameters.append(FieldDefinition.from_dict(param_def))

        return cls(
            group_name,
            group_id,
            tag_name,
            tag_index,
            description,
            tuple(parameters),
        )
