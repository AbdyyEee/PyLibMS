from __future__ import annotations

import string
from types import MappingProxyType
from typing import Generator, TypeAlias, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from lms.flowchart.msbf import MSBF

import lms.flowchart.definitions.lms_nodeexceptions as node_exceptions
from lms.common.field.lms_datatype import LMS_DataType, verify_number_from_datatype
from lms.common.field.lms_field import LMS_FieldMap
from lms.common.lms_exceptions import LMS_Error
from lms.flowchart.definitions.node_type import LMS_NodeType, LMS_NodeParameterType

from lms.flowchart.source_resolver import SourceResolver
from lms.message.lms_messagetext import LMS_MessageText
from lms.message.msbt import MSBT
from lms.message.msbtentry import MSBTEntry
from lms.titleconfig.definitions.nodes import NodeDefinition

LMS_NodeParameter: TypeAlias = LMS_FieldMap | int | str | tuple[int, ...]

NO_VALUE = 0xFFFF


class LMS_BaseNode:
    """
    Class that represents common structure and methods for any LMS_Node.
    """

    def __init__(
        self,
        node_id: int,
        node_type: LMS_NodeType,
        parameter_type: LMS_NodeParameterType,
        parameter_value: LMS_NodeParameter | None,
    ):
        self.id = node_id
        self._node_type = node_type

        self._parameter_type = parameter_type
        self._parameter_value = parameter_value

        self._stream_next_id: int | None = None
        self._next_node: LMS_BaseNode | None = None

    def __contains__(self, node: LMS_BaseNode) -> bool:
        if self is node:
            return True

        for descendent in self.get_descendents():
            if descendent is node:
                return True

        return False

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
            raise TypeError(
                "Unable to set parameter values when there is no parameter!"
            )

        if isinstance(self._parameter_value, LMS_FieldMap):
            raise ValueError(
                "Edit a parameter value through the value property of a field!"
            )

        if not isinstance(value, self._parameter_type.builtin_type):
            raise TypeError(
                f"Wrong value provided! Expected {self._parameter_type.builtin_type} got {type(value)}"
            )

        match self._parameter_type:
            case LMS_NodeParameterType.STRING:
                self._parameter_value = value
            case LMS_NodeParameterType.PARAM_32_0 | LMS_NodeParameterType.PARAM_32_1:
                verify_number_from_datatype(value, LMS_DataType.UINT32)
                self._parameter_value = value
            case _:
                for i, parameter in enumerate(value):
                    verify_number_from_datatype(
                        parameter,
                        self._parameter_type.sliced_datatype[self._parameter_type][i],
                    )

        self._parameter_value = value

    def set_next_node(self, node: LMS_BaseNode | None) -> LMS_BaseNode | None:
        """
        Set the next node for the instance.

        :param node: the node object, None for no next node.
        """
        self._next_node = node
        return node

    def get_descendents(self) -> Generator[LMS_BaseNode, None, None]:
        """Implementation of iterative DFS that yields descendents from a node."""
        visited = set()
        stack: list[LMS_BaseNode | None] = [self]

        while stack:
            current = stack.pop()

            if current is None:
                continue

            if current in visited:
                continue

            visited.add(current)
            yield current

            match current:
                # Prevent adding the entire next flowchart
                case LMS_JumpNode():
                    continue
                case LMS_BranchNode():
                    for node in current.branches.values():
                        if node is None:
                            continue

                        stack.append(node)
                case _:
                    if current.next_node is None:
                        continue

                    stack.append(current.next_node)


class LMS_MessageNode(LMS_BaseNode):
    """
    Class that represents a message node. Node utilized in junction with MSBT entries.
    """

    def __init__(
        self,
        node_id: int,
        msbt_index: int,
        label_index: int,
        source_resolver: SourceResolver | None = None,
    ):
        super().__init__(
            node_id,
            LMS_NodeType.MESSAGE,
            LMS_NodeParameterType.NONE,
            None,
        )

        self.msbt_index = msbt_index
        self.label_index = label_index
        self._source_resolver = source_resolver

    @property
    def msbt_name(self) -> str:
        """Name of the msbt resolved from the project."""
        ...

    @property
    def msbt(self) -> MSBT:
        """MSBT instance the node reference."""
        if self._source_resolver is None:
            raise ValueError("No message root and project were provided!")

        if not self._source_resolver.message_root:
            raise ValueError("No message root was provided!")

        if not self._source_resolver.project:
            raise ValueError("No project was provided!")

        return self._source_resolver.resolve_msbt_index(self.msbt_index)

    @property
    def msbt_entry(self) -> MSBTEntry:
        """The MSBTEntry instance tied to the node."""
        return self.msbt[self.label_index]

    @property
    def message_text(self) -> LMS_MessageText:
        """Message text tied to this node."""
        return self.msbt_entry.message

    def set_msbt_entry(self, entry: MSBTEntry) -> None:
        """
        Sets the entry of the MSBT file.

        :param entry: the entry of the file.
        """
        if entry not in self.msbt.entries:
            raise ValueError(f"This entry does not exist in the MSBT!")
        self.label_index = self._msbt.entries.index(entry)


class LMS_BranchNode(LMS_BaseNode):
    """
    Class that represents a branch node.
    """

    def __init__(
        self,
        node_id,
        parameter_type: LMS_NodeParameterType,
        parameter_value: LMS_NodeParameter,
        condition_id: int,
        definition: NodeDefinition | None = None,
    ):
        super().__init__(
            node_id,
            LMS_NodeType.BRANCH,
            parameter_type,
            parameter_value,
        )

        self._condition_id = condition_id
        self._branches: dict[int, LMS_BaseNode | None] = {}
        self._definition = definition

    def __repr__(self):
        if self._definition is None:
            return super().__repr__()
        return f"{self._definition.name}({ {field.name: field.value for field in self._parameter_value} } {self.id}"

    def set_next_node(self, node: LMS_BaseNode | None) -> LMS_BaseNode | None:
        raise NotImplementedError(
            "Use function set_branch_case to alter the flow of a branch node!"
        )

    @property
    def definition(self) -> NodeDefinition | None:
        """The definition of the node if provided."""
        return self._definition

    @property
    def name(self) -> str:
        """Returns the name of the node. Must have provided a node configuration when reading the file."""
        if self._definition is None:
            raise LMS_Error(
                "Unable to access the name of the node without a definition set!"
            )

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
    def branches(self) -> Mapping[int, LMS_BaseNode | None]:
        """The node branches."""
        return MappingProxyType(self._branches)

    def get_case_options(
        self, compress_shared_references: bool = False
    ) -> list[tuple[tuple[int, ...], str, LMS_BaseNode | None]]:
        """
        Retrieves the cases from this node formatted with the proper messages.

        If a definition is provided, and either ``case_format`` or ``case_options`` are provided, the resulting
        message will utilize those values to format the message.

        :param compress_shared_references: whether to compress shared references into one case.
        """
        result = []
        case_map: dict[LMS_BaseNode | None, list[int]] = {}

        for case, branch in self._branches.items():
            case_map.setdefault(branch, []).append(case)

        if self.definition is not None:
            definition: NodeDefinition = self.definition

            if definition.enum_options:
                for case, branch in self._branches.items():
                    case_format = definition.enum_options.get(
                        case,
                        None,
                    )

                    if case_format is None:
                        formatted_message = f"Case {case}"
                    else:
                        formatted_message = self._format_case_message(case, case_format)

                    result.append(((case,), formatted_message, branch))

                return result

            if definition.case_format is not None:
                if compress_shared_references:
                    for branch, cases in case_map.items():
                        case_message = self._format_case_message(
                            merge_shared_cases(cases), definition.case_format
                        )
                        result.append((tuple(cases), case_message, branch))
                else:
                    for case, branch in self._branches.items():
                        case_message = self._format_case_message(
                            case, definition.case_format
                        )
                        result.append(((case,), case_message, branch))

                return result

        if compress_shared_references:
            for branch, cases in case_map.items():
                case_message = (
                    f"Case {cases[0]}"
                    if len(cases) == 1
                    else f"Cases {merge_shared_cases(cases)}"
                )
                result.append((tuple(cases), case_message, branch))
        else:
            for case, branch in self._branches.items():
                case_message = f"Case {case}"
                result.append(((case,), case_message, branch))

        return result

    def _format_case_message(self, case_prefix: str, case_format: str):
        prefix = string.Template(case_format)

        # Unpack dict for formatting $case and $param formats
        # Allows inserting parameter values dynamically into the case message
        # This will run normally even without any valid formatting
        string_map = {}
        for param_definition in self.definition.parameter_definitions:
            string_map[param_definition.name] = self.parameter_value[
                param_definition.name
            ].value

        string_map["case"] = case_prefix
        return prefix.substitute(**string_map)

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


class LMS_EventNode(LMS_BaseNode):
    """
    Class that represents an event node. Node utilized for in-game actions.
    """

    def __init__(
        self,
        node_id: int,
        parameter_type: LMS_NodeParameterType,
        parameter_value: LMS_FieldMap | int | str | tuple[int, ...],
        event_id: int,
        definition: NodeDefinition | None = None,
    ):
        super().__init__(node_id, LMS_NodeType.EVENT, parameter_type, parameter_value)

        self._event_id = event_id
        self._definition = definition

    def __repr__(self):
        if self._definition is None:
            return super().__repr__()
        return f"{self._definition.name}({ {field.name: field.value for field in self._parameter_value} } {self.id}"

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
    def event_id(self) -> int:
        """The identifier to determine which action to run."""
        return self._event_id


class LMS_EntryNode(LMS_BaseNode):
    """
    Class that represents an entry node. Node that is at the start of a flowchart.
    """

    def __init__(self, node_id: int, name: str = ""):
        super().__init__(node_id, LMS_NodeType.ENTRY, LMS_NodeParameterType.NONE, None)
        self.name = name


class LMS_JumpNode(LMS_BaseNode):
    """
    Class that represents a jump node. Node that jumps to another flowchart.
    """

    def __init__(
        self,
        node_id: int,
        msbf_index: int | None,
        source_resolver: SourceResolver | None,
        next: LMS_EntryNode = None,
    ):
        super().__init__(node_id, LMS_NodeType.JUMP, LMS_NodeParameterType.NONE, None)

        self._next_entry = next
        self.msbf_index = msbf_index
        self._source_resolver = source_resolver

    @property
    def next_entry(self) -> LMS_EntryNode | None:
        """The pointing entry node."""
        return self._next_entry

    @property
    def msbf(self) -> MSBF:
        """MSBF instance the node reference."""
        if self._source_resolver is None:
            raise ValueError("No message root and project were provided!")

        if not self._source_resolver.message_root:
            raise ValueError("No message root was provided!")

        if not self._source_resolver.project:
            raise ValueError("No project was provided!")

        return self._source_resolver.resolve_msbf_index(self.msbf_index)

    @next_entry.setter
    def next_entry(self, node: LMS_EntryNode | None) -> None:
        if isinstance(node, LMS_EntryNode) or node is None:
            super().set_next_node(node)
            self._next_entry = node
        else:
            raise TypeError(
                "The next pointing entry node must be a LMS_EntryNode or None"
            )


def verify_parameter_structure(
    value: int | tuple[int, ...] | str, parameter_type: LMS_NodeParameterType
) -> None:
    if parameter_type is LMS_NodeParameterType.NONE:
        raise node_exceptions.LMS_NodeInvalidParameterTypeError(
            "There must be a parameter type!"
        )

    if not isinstance(value, parameter_type.builtin_type):
        raise node_exceptions.LMS_NodeInvalidParameterValueError(
            f"Parameter type {parameter_type} expects type {parameter_type.builtin_type},"
            f" but got {type(value)}."
        )

    if isinstance(value, tuple) and len(value) != parameter_type.value_count:
        raise node_exceptions.LMS_NodeMissingParameterValueError(
            f"Parameter type {parameter_type} expects {parameter_type.value_count} parameter values, got {len(value)}!"
        )


# https://stackoverflow.com/a/69711845
def merge_shared_cases(cases: list[int]) -> str:
    result = []
    values = sorted(cases)

    first = last = values[0]

    for i in values[1:]:
        if i - last > 1:
            if first == last:
                result.append(str(first))
            else:
                result.append(f"{first}-{last}")
            first = i
        last = i

    if first == last:
        result.append(str(first))
    else:
        result.append(f"{first}-{last}")

    return ", ".join(result)
