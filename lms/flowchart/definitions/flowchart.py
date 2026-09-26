from types import MappingProxyType
from typing import Callable, Iterator

from lms.flowchart.definitions.node import LMS_EntryNode, LMS_BranchNode, LMS_BaseNode


class LMS_Flowchart:
    """Class that represents a flowchart in a MSBF file."""

    def __init__(
            self, entry_point: LMS_EntryNode, id_generator: Callable[[], int]
    ) -> None:
        self._entry_node = entry_point
        self._nodes: dict[int, LMS_BaseNode] = {}
        self._id_generator = id_generator

        if entry_point is not None:
            for node in entry_point.get_descendents():
                self._nodes[node.id] = node

    def __iter__(self) -> Iterator[LMS_BaseNode]:
        return iter(self._nodes.values())

    def __len__(self) -> int:
        return len(self._nodes)

    def __getitem__(self, node_id: int) -> LMS_BaseNode:
        return self._nodes[node_id]

    @property
    def name(self) -> str:
        """The name of the flowchart."""
        return self._entry_node.flowchart_name

    @name.setter
    def name(self, name: str) -> None:
        self._entry_node.flowchart_name = name

    @property
    def entry_point(self) -> LMS_EntryNode:
        """The starting node for the flowchart."""
        return self._entry_node

    @property
    def nodes(self) -> MappingProxyType[int, LMS_BaseNode]:
        """All nodes in the flowchart instance."""
        return MappingProxyType(self._nodes)

    def register_node(self, node: LMS_BaseNode) -> None:
        """
        Registers a node to the flowchart.

        :param node: the node to add.
        """
        if node.id is None:
            raise ValueError("Node must be registered to an MSBF file before a flowchart!")

        self._nodes[node.id] = node

    def deregister_node(self, node_id: int) -> None:
        """
        Deletes a node from the flowchart.

        :param node_id: the id of the node to delete.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node id '{node_id}' does not exist in this flowchart!")

        deleted_node = self._nodes[node_id]

        if deleted_node is self._entry_node:
            raise ValueError("The entry node cannot be deleted!")

        next_node = deleted_node.next_node

        # There may be gaps in IDs, this is intended
        # Lazy processing is better instead of constant realignment
        # IDs are realigned during writing, but do not alter the current state
        for node in self._nodes.values():
            if node is deleted_node:
                continue

            if node.next_node is deleted_node:
                node.set_next_node(next_node)

            if isinstance(node, LMS_BranchNode):
                for case, branch in node.branches.items():
                    if branch is deleted_node:
                        node.set_branch_case(case, next_node)

        del self._nodes[node_id]

    def get_dangling_nodes(self) -> list[LMS_BaseNode]:
        """
        Retrieves all the nodes that do not have a parent in the flowchart.
        """
        valid_nodes = set()

        for node in self._entry_node.get_descendents():
            valid_nodes.add(node)

        dangling_nodes = set(self._nodes.values()) - valid_nodes
        return list(dangling_nodes)
