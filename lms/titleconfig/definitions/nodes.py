from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping, Any

from lms.common.field.lms_datatype import LMS_DataType
from lms.flowchart.definitions.node_type import LMS_NodeType, LMS_NodeParameterType
from lms.titleconfig.definitions.field import FieldDefinition


class NodeConfig:
    """
    Class that represents a node configuration.
    """

    def __init__(self, branch_definitions: dict[int, tuple[NodeDefinition, ...]] = None,
                 event_definitions: dict[int, tuple[NodeDefinition, ...]] = None):

        self._branch_definitions = branch_definitions or {}
        self._event_definitions = event_definitions or {}

    @property
    def branch_definitions(self) -> Mapping[str, tuple[NodeDefinition, ...]]:
        """Mapping of branch definitions for this configuration."""
        return MappingProxyType(self._branch_definitions)

    @property
    def event_definitions(self) -> Mapping[str, tuple[NodeDefinition, ...]]:
        """Mapping of branch definitions for this configuration."""
        return self._event_definitions

    def add_definition(self, node_type: LMS_NodeType.BRANCH | LMS_NodeType.EVENT, data: Mapping[str, Any]) -> None:
        """
        Adds a ``NodeDefinition`` object to the configuration.

        :param node_type: The type of the definition.
        :param data: The node definition data.
        """
        node_id = data["id"]
        definition = NodeDefinition.from_dict(node_id, node_type, data)
        attr = getattr(self, "_branch_definitions" if node_type is LMS_NodeType.BRANCH else "_event_definitions")
        attr[node_id] = (definition,)

        if node_id in attr:
            attr[node_id] = attr[node_id] + (definition,)
        else:
            attr[node_id] = (definition,)

    def get_definition(
            self,
            identifier: int,
            node_type: Literal[LMS_NodeType.BRANCH] | Literal[LMS_NodeType.EVENT],
            parameter_type: LMS_NodeParameterType = None,
    ) -> NodeDefinition:
        """
        Retrieves a node definition by its ID and the type.

        :param identifier: The condition/event identifier of the node.
        :param node_type: The type of the node.
        :param parameter_type: The parameter of the node.
        """
        match node_type:
            case LMS_NodeType.BRANCH:
                if identifier not in self.branch_definitions:
                    return None
                definition = self.branch_definitions[identifier]
            case LMS_NodeType.EVENT:
                if identifier not in self.event_definitions:
                    return None
                definition = self.event_definitions[identifier]
            case _:
                raise TypeError(
                    f"You may not use '{node_type}' with a node configuration."
                )
        for variant in definition:
            if variant.parameter_type is parameter_type:
                return variant

        return None


@dataclass(frozen=True)
class NodeDefinition:
    """Class that represents a node definition."""

    name: str
    id: int
    description: str
    type: LMS_NodeType.BRANCH | LMS_NodeType.EVENT
    parameter_type: LMS_NodeParameterType
    parameter_definitions: tuple[FieldDefinition, ...]
    case_format: str
    enum_options: Mapping[int, str]
    next_node_dependency: bool = False

    @classmethod
    def from_dict(cls, identifier: int, node_type: LMS_NodeType, data: dict) -> NodeDefinition | None:

        name, description = data["name"], data.get("description", "")
        converted_parameters: list[FieldDefinition] = []

        parameter_type = data.get("parameter_type")

        if parameter_type is not None:
            parameter_type = LMS_NodeParameterType.from_string(parameter_type)

        for i, parameter in enumerate(data.get("parameters", ())):
            datatype_from_dict = parameter.get("datatype", None)

            enum_members = MappingProxyType(parameter.get("enum_members", {}))

            if datatype_from_dict is None:
                if parameter_type is LMS_NodeParameterType.STRING:
                    datatype_from_dict = LMS_DataType.STRING
                else:
                    datatype_from_dict = parameter_type.sliced_datatype[i]
                definition = FieldDefinition(parameter["name"], description, datatype_from_dict, enum_members)
            else:
                definition = FieldDefinition(
                    parameter["name"],
                    description,
                    LMS_DataType.from_string(datatype_from_dict),
                    enum_members,
                )

            converted_parameters.append(definition)

        # case_format/enum_options is only for branch nodes
        if "case_format" in data and "enum_options" in data:
            raise ValueError(
                "There may only be one of enum_options and options in the definition."
            )

        if (enum_options := data.get("enum_options", "")) and node_type is LMS_NodeType.EVENT:
            raise ValueError(f"There may only be options for branch nodes for definition '{name}'")

        if (case_format := data.get("case_format", "")) and node_type == LMS_NodeType.EVENT:
            raise ValueError(f"There may only be case_format for branch nodes, '{name}' is an event definition!")

        return NodeDefinition(
            name=name,
            id=identifier,
            description=data.get("description", ""),
            type=node_type,
            parameter_type=parameter_type,
            parameter_definitions=converted_parameters,
            case_format=case_format,
            enum_options=enum_options,
            next_node_dependency=data.get("next_node_dependency", False),
        )
