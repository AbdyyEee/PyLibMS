from types import MappingProxyType
from typing import Mapping, Iterator

from lms.common.lms_fileinfo import LMS_FileInfo
from lms.fileio.encoding import FileEncoding
from lms.flowchart.definitions.flowchart import LMS_Flowchart
from lms.flowchart.definitions.node import LMS_EntryNode, LMS_JumpNode, LMS_BranchNode, LMS_BaseNode


class MSBF:
    """
    Class that represents a MSBF instance.

    ======
    Usages
    ======
    https://github.com/AbdyyEee/PylibMS/wiki/MSBF

    =========
    File Info
    =========
    https://nintendo-formats.com/libs/lms/msbf.html
    """

    MAGIC = "MsgFlwBn"
    DEFAULT_SLOT_COUNT = 59

    def __init__(
            self, info: LMS_FileInfo | None = None, flowcharts: list[LMS_Flowchart] = None
    ):
        self._info = info if info is not None else LMS_FileInfo()

        # While unlikely to vary, and have yet to find a file that changes the slot count (unlike MSBT)
        # it is wiser to store an editable attribute just in case a game decides to vary the amount.
        self.slot_count = MSBF.DEFAULT_SLOT_COUNT

        self._flowcharts: dict[int, LMS_EntryNode] = flowcharts or {}
        self._nodes: dict[int, LMS_BaseNode] = {}
        self._global_node_id = 0

    def __contains__(self, node: LMS_BaseNode) -> bool:
        return node.id in self._nodes

    def __getitem__(self, node_id: int) -> LMS_BaseNode:
        return self._nodes[node_id]

    def __len__(self) -> int:
        return len(self._flowcharts)

    def __iter__(self) -> Iterator[LMS_EntryNode]:
        return iter(self._nodes.values())

    @classmethod
    def new(
            cls,
            is_big_endian: bool = False,
            encoding: FileEncoding = FileEncoding.UTF16,
            version: int = 3,
            section_count: int = 2,
    ):
        """
        Create a new MSBF instance.

        :param is_big_endian: if the file is big endian.
        :param encoding: the file encoding.
        :param version: the file version.
        :param section_count: the number of sections.

        """
        return MSBF(LMS_FileInfo(is_big_endian, encoding, version, section_count))

    @property
    def info(self) -> LMS_FileInfo:
        """The file info for the MSBT instance."""
        return self._info

    @property
    def nodes(self) -> Mapping[int, LMS_BaseNode]:
        """Global node map for the file."""
        return MappingProxyType(self._nodes)

    @property
    def flowcharts(self) -> Mapping[str, LMS_EntryNode]:
        """The flowcharts of the MSBF instance."""
        return MappingProxyType(self._flowcharts)

    @property
    def entry_nodes(self) -> tuple[LMS_EntryNode, ...]:
        """The entry nodes of the MSBF instance."""
        return tuple(self._flowcharts.values())

    def get_flowchart_references(self, node: LMS_BaseNode) -> tuple[LMS_EntryNode, ...]:
        """
        Determines which flowcharts contain this node.

        :param node: The node to find references for.
        """
        references = []
        for entry_node in self:
            if node in entry_node:
                references.append(entry_node)
        return references

    def register_node(self, node: LMS_BaseNode) -> None:
        """
        Registers a node to the MSBF instance.

        :param node: The node to register.
        """
        if not isinstance(node, LMS_BaseNode):
            raise TypeError(
                f"Node type '{type(node).__name__}' is not a child of LMS_BaseNode!"
            )

        if node.id in self._nodes:
            raise ValueError(
                f"Node of ID '{node.id}' is already registered to this flowchart!"
            )

        node.id = self._generate_next_id()
        self._nodes[node.id] = node

    def destroy_node(self, to_delete: LMS_BaseNode) -> None:
        """
        Destroys a node and all its references.

        :param to_delete: The node to delete.
        """
        if to_delete not in self._nodes:
            raise KeyError(f"Node id '{to_delete.id}' does not exist in this flowchart!")

        if isinstance(to_delete, LMS_EntryNode):
            raise ValueError("Entry nodes cannot be deleted!")

        # Check each node and all nested branches for the node, and destroy it
        # If in a branch, the node is set to NONE/END
        # Otherwise the next node of to_delete is the new next node of the child
        new_next = to_delete.next_node
        for node in self:
            if isinstance(node, LMS_BranchNode):
                for case, branch in node.branches:
                    if branch is None or branch != to_delete:
                        continue
                    node.set_branch_case(case, None)
                continue

            if node.next_node == to_delete:
                node.set_next_node(new_next)

        del self._nodes[to_delete.id]

    def add_flowchart(
            self, name: str, entry_point: LMS_EntryNode = None
    ) -> LMS_EntryNode:
        """
        Add a flowchart to the MSBF instance.

        :param name: The name of the new flowchart.
        :param entry_point: The entry point of the new flowchart. If not provided, the method creates one.
        """
        if name in self.flowcharts:
            raise KeyError(f"Flowchart with name '{name}' already exists!")

        if entry_point is None:
            entry_point = LMS_EntryNode(self._generate_next_id(), name)

        for node in entry_point.get_descendents():
            if node.id in self._nodes:
                continue
            self._nodes[node.id] = node

        self._flowcharts[name] = entry_point
        self._nodes = dict(sorted(self._nodes.items()))

        # Node IDs may not be sequential after user additions/deletions, so we track the absolute max value of
        # all nodes and store it so that _generate_next_id can set any IDs added via the flowchart correctly.
        self._global_node_id = max(self._nodes, default=-1) + 1

        return entry_point

    def delete_flowchart(self, name: str):
        """
        Delete a flowchart from the MSBF instance.

        All jump nodes that reference the flowchart will have their flowchart set to None.
        """

        if name not in self.flowcharts:
            raise KeyError(f"Flowchart with name {name} does not exist!")

        entry_point = self.flowcharts[name].entry_point

        is_valid_jump = lambda n: isinstance(n, LMS_JumpNode) and n.next_entry == entry_point

        for flowchart in self:
            for node in flowchart.nodes.copy().values():
                if isinstance(node, LMS_BranchNode):
                    for case, branch in node.branches.items():
                        if is_valid_jump(branch):
                            branch.next_flowchart = None
                    continue

                if is_valid_jump(node):
                    node.next_entry = None

    def _generate_next_id(self) -> int:
        next_id = self._global_node_id
        self._global_node_id += 1
        return next_id
