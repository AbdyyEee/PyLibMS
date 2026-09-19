from __future__ import annotations

from dataclasses import dataclass

from lms.common.field.lms_datatype import LMS_DataType
from lms.flowchart.definitions.node_type import LMS_NodeType, LMS_NodeParameterType
from lms.titleconfig.definitions.value import ValueDefinition


@dataclass(frozen=True)
class NodeConfig:
    """
    Class that represents a node configuration.
    """

    branch_definitions: dict[int, NodeDefinition | tuple[NodeDefinition, ...]]
    event_definitions: dict[int, NodeDefinition, tuple[NodeDefinition, ...]]

    def get_definition(self, id: int,
                       node_type: LMS_NodeType.BRANCH | LMS_NodeType.EVENT,
                       parameter_type: LMS_NodeParameterType) -> NodeDefinition:
        """Gets a node definition by its ID and the type."""
        match node_type:
            case LMS_NodeType.BRANCH:
                if id not in self.branch_definitions:
                    return None
                definition = self.branch_definitions[id]
            case LMS_NodeType.EVENT:
                if id not in self.event_definitions:
                    return None
                definition = self.event_definitions[id]
            case _:
                raise TypeError(f"You may not use '{node_type}' with a node configuration.")

        if isinstance(definition, tuple):
            for variant in definition:
                if variant.parameter_type is parameter_type:
                    return variant

            return None

        if definition.parameter_type is parameter_type:
            return definition

        return None


@dataclass(frozen=True)
class NodeDefinition:
    """Class that represents a node definition."""

    name: str
    id: int
    description: str
    type: LMS_NodeType.BRANCH | LMS_NodeType.EVENT
    parameter_type: LMS_NodeParameterType
    parameter_definitions: tuple[ValueDefinition, ...]
    case_format: str | None
    case_options: dict[int, str]
    next_node_dependency: bool = False

    @classmethod
    def from_dict(cls, id: int, node_type: LMS_NodeType, data: dict) -> NodeDefinition:

        description = data.get("description", "")
        converted_parameters: list[ValueDefinition] = []
        parameter_type = LMS_NodeParameterType.from_string(data["parameter_type"])

        for i, parameter in enumerate(data["parameters"]):
            datatype_from_dict = parameter.get("datatype", None)

            list_items = parameter.get("list_items", [])

            if datatype_from_dict is None:
                match parameter_type:
                    case LMS_NodeParameterType.PARAM_32_0 | LMS_NodeParameterType.PARAM_32_1:
                        datatype_from_dict = LMS_DataType.UINT32
                    case LMS_NodeParameterType.PARAM_16_16:
                        datatype_from_dict = (LMS_DataType.UINT16, LMS_DataType.UINT16)[i]
                    case LMS_NodeParameterType.PARAM_16_8_8:
                        datatype_from_dict = (LMS_DataType.UINT16, LMS_DataType.UINT8, LMS_DataType.UINT8)[i]
                    case LMS_NodeParameterType.PARAM_8_8_16:
                        datatype_from_dict = (LMS_DataType.UINT8, LMS_DataType.UINT8, LMS_DataType.UINT16)[i]
                    case LMS_NodeParameterType.PARAM_8_8_8_8:
                        datatype_from_dict = \
                            (LMS_DataType.UINT8, LMS_DataType.UINT8, LMS_DataType.UINT8, LMS_DataType.UINT8)[i]
                    case LMS_NodeParameterType.STRING:
                        datatype_from_dict = LMS_DataType.STRING
                definition = ValueDefinition(parameter["name"], description, datatype_from_dict,
                                             list_items)
            else:
                definition = ValueDefinition(parameter["name"], description,
                                             LMS_DataType.from_string(datatype_from_dict),
                                             list_items)

            converted_parameters.append(definition)

        # case_format is only for branch nodesa
        if "case_format" in data and "case_options" in data:
            raise ValueError("There may only be one of case_format and options in the definition.")

        if (options := data.get("case_options", None)) is not None and type == LMS_NodeType.EVENT:
            raise ValueError("There may only be options for branch nodes!")

        if (case_format := data.get("case_format", None)) is not None and type == LMS_NodeType.EVENT:
            raise ValueError("There may only be case_format for branch nodes!")

        return NodeDefinition(
            name=data["name"],
            id=id,
            description=data.get("description", ""),
            type=node_type,
            parameter_type=parameter_type,
            parameter_definitions=converted_parameters,
            case_format=case_format,
            case_options=options,
            next_node_dependency=data.get("next_node_dependency", False)
        )
