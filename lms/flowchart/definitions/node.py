from __future__ import annotations

from collections import deque
from types import MappingProxyType
from typing import Generator

import lms.flowchart.definitions.lms_nodeexceptions as node_exceptions
from lms.common.field.lms_datatype import LMS_DataType
from lms.common.field.lms_field import LMS_FieldMap, verify_number_from_datatype
from lms.common.lms_exceptions import LMS_Error
from lms.flowchart.definitions.node_type import LMS_NodeType, LMS_NodeParameterType
from lms.message.msbt import MSBT
from lms.message.msbtentry import MSBTEntry
from lms.titleconfig.definitions.nodes import NodeDefinition

type LMS_NodeParameter = LMS_FieldMap | int | str | tuple[int, ...]

NO_NEXT_NODE = -1


class LMS_BaseNode:
    """
    Class that represents common structure and methods for a LMS_Node.
    """

    def __init__(self,
                 id: int | None,
                 node_type: LMS_NodeType,
                 parameter_type: LMS_NodeParameterType,
                 parameter_value: LMS_NodeParameter | None,
                 stream_next_id: int | None = None):
        self.id = id
        self._node_type = node_type

        self._parameter_type = parameter_type
        self._parameter_value = parameter_value

        self._stream_next_id: int | None = stream_next_id
        self._next_node: LMS_BaseNode | None = None

    @property
    def type(self) -> LMS_NodeType:
        """The type of the node."""
        return self._node_type

    @property
    def next_node(self) -> LMS_BaseNode | None:
        """The next node instance."""
        return self._next_node

    @property
    def next_node_id(self) -> int | None:
        """The next node id of the node."""
        if self._next_node is not None:
            return self._next_node.id
        return self._stream_next_id

    @property
    def parameter_type(self) -> LMS_NodeParameterType:
        """The parameter type of the node."""
        return self._parameter_type

    @property
    def parameter_value(self) -> LMS_NodeParameter | None:
        """The parameter value of the node."""
        return self._parameter_value

    @parameter_value.setter
    def parameter_value(self, value: LMS_NodeParameter):
        if self._parameter_type == LMS_NodeParameterType.NONE:
            raise TypeError("Unable to set parameter values when there is no parameter!")

        if isinstance(self._parameter_value, LMS_FieldMap):
            raise ValueError("Edit a parameter value through the value property of a field!")

        if not isinstance(value, self._parameter_type.builtin_type):
            raise TypeError(f"Wrong value provided! Expected {self._parameter_type.builtin_type} got {type(value)}")

        sliced_datatype = {
            LMS_NodeParameterType.PARAM_16_16: (LMS_DataType.UINT16, LMS_DataType.UINT16),
            LMS_NodeParameterType.PARAM_16_8_8: (LMS_DataType.UINT16, LMS_DataType.UINT8, LMS_DataType.UINT8),
            LMS_NodeParameterType.PARAM_8_8_16: (LMS_DataType.UINT8, LMS_DataType.UINT8, LMS_DataType.UINT16),
            LMS_NodeParameterType.PARAM_8_8_8_8: (LMS_DataType.UINT8, LMS_DataType.UINT8, LMS_DataType.UINT8,
                                                  LMS_DataType.UINT8)
        }

        match self._parameter_type:
            case LMS_NodeParameterType.STRING:
                self._parameter_value = value
            case LMS_NodeParameterType.PARAM_32_0 | LMS_NodeParameterType.PARAM_32_1:
                verify_number_from_datatype(value, LMS_DataType.UINT32)
                self._parameter_value = value
            case _:
                for i, parameter in enumerate(value):
                    verify_number_from_datatype(parameter, sliced_datatype[self._parameter_type][i])

        self._parameter_value = value

    def set_next_node(self, node: LMS_BaseNode | None) -> LMS_BaseNode | None:
        """Set the next node for the instance.

        :param node: the node object, None for no next node."""
        # Once next_node is properly set, stream_id is never accessed again
        # While it does become stale, there is no point to altering it afterward
        self._next_node = node
        return node

    def get_children(self) -> Generator[LMS_BaseNode | None, None, None]:
        """A generator for all the connected nodes."""
        if self._next_node is not None:
            yield self.next_node

    def get_descendents(self) -> Generator[LMS_BaseNode, None, None]:
        """Implementation of BFS that yields descendents from a node."""
        visited: set[int] = set()
        stack = deque([self])

        while stack:
            node = stack.popleft()

            # Track memory address of the node in case the ID is unregistered
            if node is None or id(node) in visited:
                continue

            visited.add(id(node))
            yield node

            # Prevent adding the entire next flowchart
            if isinstance(node, LMS_JumpNode):
                continue

            for child in node.get_children():
                if child is None:
                    continue

                stack.append(child)


class LMS_MessageNode(LMS_BaseNode):
    """
    Class that represents a message node. Node utilized in juction with MSBT entries.
    """

    def __init__(self,
                 id: int | None,
                 stream_next_node: int,
                 msbt_index: int,
                 label_index: int,
                 msbt: MSBT | None = None
                 ):
        super().__init__(
            id,
            LMS_NodeType.MESSAGE,
            LMS_NodeParameterType.NONE,
            None,
            stream_next_node
        )

        self.msbt_index = msbt_index
        self.label_index = label_index
        self._msbt = msbt

    @classmethod
    def new(cls, file_index: int, label_index: int):
        """
        Creates a new LMS_MessageNode.

        :param file_index: index of the MSBT file in a folder/archive.
        :param label_index: index of the label entry in that MSBT file.
        """
        return cls(None, None, file_index, label_index)

    @classmethod
    def new_msbt(cls, file_index: int, entry: MSBTEntry, msbt: MSBT):
        """
        Creates a new LMS_MessageNode given a MSBT object.

        :param file_index: index of the MSBT file in a folder/archive.
        :param entry: the MSBTEntry object to reference.
        :param msbt: the MSBT file.
        """
        return cls(None, None, file_index, msbt.entries.index(entry), msbt)

    @property
    def msbt(self) -> MSBT | None:
        """MSBT instance the node references. Optional, and must be set with `set_msbt` or by  providing a MSBT file on reading."""
        return self._msbt

    @property
    def msbt_entry(self) -> MSBTEntry:
        """The MSBTEntry instance tied to the message node."""
        if self._msbt is None:
            raise LMS_Error("There is no MSBTEntry associated with this node!")

        return self._msbt.get_entry_by_index(self.label_index)


class LMS_BranchNode(LMS_BaseNode):
    """
    Class that represents a branch node.
    """

    def __init__(self,
                 id: int,
                 parameter_type: LMS_NodeParameterType,
                 parameter_value: LMS_NodeParameter,
                 condition_id: int,
                 definition: NodeDefinition | None = None):
        super().__init__(
            id,
            LMS_NodeType.BRANCH,
            parameter_type,
            parameter_value,
            NO_NEXT_NODE
        )

        self._condition_id = condition_id
        self._branches: dict[int, LMS_BaseNode | None] = {}
        self._definition = definition

    @classmethod
    def new(cls,
            parameter_type: LMS_NodeParameterType,
            parameter_value: LMS_NodeParameter,
            condition_id: int,
            ):
        """
        Instantiates a new branch node.

        :param parameter_type: the parameter type.
        :param parameter_value: the parameter value.
        :param condition_id: the condition id.
        """
        return cls(None, parameter_type, parameter_value, condition_id)

    @classmethod
    def new_from_definition(cls,
                            definition: NodeDefinition,
                            **parameter_values: str | bool | float | bytes,
                            ):
        """
        Instantiates a new branch node from a definition.

        :param definition: the node definition.
        :param parameter_values: keyword arguments of parameters.
        """
        converted = LMS_FieldMap.from_dict(parameter_values, definition.parameter_definitions)
        return cls(None, definition.parameter_type, converted, definition.id)

    @property
    def definition(self) -> NodeDefinition | None:
        """The definition of the node if provided."""
        return self._definition

    @property
    def name(self) -> str:
        """Returns the name of the node. Must have provided a node configuration when reading the file."""
        if self._definition is None:
            raise LMS_Error("Unable to access the name of the node without a definition set!")

        return self._definition.name

    @property
    def condition_id(self):
        """Identifier that determines the branch condition."""
        return self._condition_id

    @property
    def case_count(self):
        """The amount of cases this branch node evaluates."""
        return len(self._branches)

    @property
    def branches(self) -> MappingProxyType[int, LMS_BaseNode | None]:
        """The node branches."""
        return MappingProxyType(self._branches)

    def add_branch(self, node: LMS_BaseNode | None) -> None:
        """
        Adds a branch to the node.

        :param node: the node to add.
        """
        self._branches[self.case_count] = node

    def add_branches(self, *nodes: LMS_BaseNode | None) -> None:
        """
        Adds several branches to the node.

        :param nodes: arguments of nodes to add.
        """
        for node in nodes:
            self.add_branch(node)

    def set_case_count(self, count: int) -> None:
        """
        Adds or truncates the branch count.

        Truncating the cases will only result in End/Undefined/None cases being removed.

        :param count: the new branch count.
        """
        case_count = len(self._branches)

        if count < self.case_count:
            for case in range(count, case_count):
                if self._branches[case] is not None:
                    raise ValueError(
                        f"Cannot remove case {case} because it references a node!"
                    )

            for case in range(case_count - 1, count - 1, -1):
                self._branches.pop(case, None)
        else:
            for case in range(case_count, count):
                self._branches[case] = None

    def set_branch_case(self, case: int, new_node: LMS_BaseNode | None) -> None:
        """
        Alters an existing branch case.

        If setting a case to a new node object, ensured it is registered in the flowchart.

        :param case: the branch case to change.
        :param new_node: the new node to set.
        """
        if case not in self._branches:
            raise KeyError(f"The case '{case}' does not exist as a branch!")

        self._branches[case] = new_node

    def get_children(self) -> Generator[LMS_BaseNode, None, None]:
        for node in self.branches.values():
            if node is not None:
                yield node


class LMS_EventNode(LMS_BaseNode):
    """
    Class that represents an event node. Node utilized for in-game actions.
    """

    def __init__(self,
                 id: int,
                 parameter_type: LMS_NodeParameterType,
                 parameter_value: LMS_FieldMap | int | str | tuple[int, ...],
                 action_id: int,
                 stream_next_id: int | None = None,
                 definition: NodeDefinition | None = None,
                 ):
        super().__init__(
            id,
            LMS_NodeType.EVENT,
            parameter_type,
            parameter_value,
            stream_next_id)

        self._action_id = action_id
        self._definition = definition

    @classmethod
    def new(cls, parameter_type: LMS_NodeParameterType, parameter_value: int | str | tuple[int, ...], action_id: int):
        """
        Instantiates a new event node.

        :param parameter_type: the parameter type.
        :param parameter_value: the parameter value.
        :param action_id: the action_id of the node.

        """
        verify_parameter_structure(parameter_value, parameter_type)
        return cls(None, parameter_type, parameter_value, action_id)

    @classmethod
    def new_from_definition(cls,
                            definition: NodeDefinition,
                            **parameter_values: str | int | str | tuple[int, ...],
                            ):
        """
        Instantiates a new event node from a definition.

        :param definition: the node definition.
        :param parameter_values: keyword arguments of parameters.
        """
        converted = LMS_FieldMap.from_dict(parameter_values, definition.parameter_definitions)
        return cls(None, definition.parameter_type, converted, definition.id)

    @property
    def definition(self) -> NodeDefinition | None:
        """The definition of the node if provided."""
        return self._definition

    @property
    def name(self) -> str | None:
        """Returns the name of the node. Must have provided a node configuration when reading the file."""
        if self._definition is None:
            return None

        return self._definition.name

    @property
    def action_id(self) -> int:
        """The identifier to determine which action to run."""
        return self._action_id


class LMS_EntryNode(LMS_BaseNode):
    """
    Class that represents an entry node. Node that is at the start of a flowchart.
    """

    def __init__(self, id: int, stream_next_id=None, flowchart_name: str = ""):
        super().__init__(
            id,
            LMS_NodeType.ENTRY,
            LMS_NodeParameterType.NONE,
            None,
            stream_next_id)

        self.flowchart_name = flowchart_name


class LMS_JumpNode(LMS_BaseNode):
    """
    Class that represents a jump node. Node that jumps to another flowchart.
    """

    def __init__(self, id: int, next_flowchart_id: int, unknown_short0a: int):
        super().__init__(
            id,
            LMS_NodeType.JUMP,
            LMS_NodeParameterType.NONE,
            None,
            next_flowchart_id)

        self.next_flowchart: LMS_EntryNode | None = None

        # TODO: Document this unknown value at 0xA in the node
        # This value is usually -1 in TL 3DS but is a set value in other games
        self.unknown_short0a = unknown_short0a

    @classmethod
    def new(cls, next_entry_point: LMS_EntryNode, unknown_short0a: int):
        """
        Instantiates a new jump node.

        :param next_entry_point: the next entry point.
        :param unknown_short0a: unknown short value. -1 if there is no value.
        """
        node = cls(None, next_entry_point.id, unknown_short0a)
        node.next_flowchart = next_entry_point
        return node

    @property
    def next_flowchart_id(self) -> int:
        """The ID of the next flowchart."""
        if self.next_flowchart is not None:
            return self.next_flowchart.id

        return self._stream_next_id

    def set_next_node(self, node: LMS_BaseNode | None) -> LMS_BaseNode | None:
        super().set_next_node(node)
        if isinstance(node, LMS_EntryNode) or node is None:
            self.next_flowchart = node
        return node


def verify_parameter_structure(value: int | tuple[int, ...] | str, parameter_type: LMS_NodeParameterType) -> None:
    if parameter_type is LMS_NodeParameterType.NONE:
        raise node_exceptions.LMS_NodeInvalidParameterTypeError("There must be a parameter type!")

    if not isinstance(value, parameter_type.builtin_type):
        raise node_exceptions.LMS_NodeInvalidParameterValueError(
            f"Parameter type {parameter_type} expects type {parameter_type.builtin_type},"
            f" but got {type(value)}.")

    if isinstance(value, tuple) and len(value) != parameter_type.value_count:
        raise node_exceptions.LMS_NodeMissingParameterValueError(
            f"Parameter type {parameter_type} expects {parameter_type.value_count} parameter values, got {len(value)}!")
