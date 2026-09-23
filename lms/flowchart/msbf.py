from types import MappingProxyType

from lms.common.lms_fileinfo import LMS_FileInfo
from lms.fileio.encoding import FileEncoding
from lms.flowchart.definitions.flowchart import LMS_Flowchart
from lms.flowchart.definitions.node import LMS_EntryNode, LMS_JumpNode, LMS_BranchNode


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
        self._flowcharts = flowcharts or []
        self._global_node_id = 0

    def __iter__(self):
        return iter(self._flowcharts)

    def __len__(self):
        return len(self._flowcharts)

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
    def flowcharts(self) -> MappingProxyType[str, LMS_Flowchart]:
        """The flowcharts of the MSBF instance."""
        return MappingProxyType(
            {flowchart.name: flowchart for flowchart in self._flowcharts}
        )

    def add_flowchart(
            self, flowchart_name: str, entry_point: LMS_EntryNode = None
    ) -> LMS_Flowchart:
        """
        Add a flowchart to the MSBF instance.

        :param flowchart_name: The name of the new flowchart.
        :param entry_point: The entry point of the new flowchart. If not provided, the method creates one.
        """
        if flowchart_name in self.flowcharts:
            raise KeyError(f"Flowchart with name '{flowchart_name}' already exists!")

        # Node IDs may not be sequential after user additions/deletions, so we track the absolute max value of
        # all nodes and store it so that _generate_next_id can set any IDs added via the flowchart correctly.
        self._global_node_id = max((node.id for flowchart in self for node in flowchart), default=1) + 1

        if entry_point is None:
            entry_point = LMS_EntryNode(self._generate_next_id(), flowchart_name)

        flowchart = LMS_Flowchart(entry_point, self._generate_next_id)
        self._flowcharts.append(flowchart)
        return flowchart

    def delete_flowchart(self, name: str):
        """
        Delete a flowchart from the MSBF instance.

        All jump nodes that reference the flowchart will have their flowchart set to None.
        """

        if name not in self.flowcharts:
            raise KeyError(f"Flowchart with name {name} does not exist!")

        entry_point = self.flowcharts[name].entry_point

        is_valid_jump = lambda n: isinstance(n, LMS_JumpNode) and n.next_flowchart == entry_point

        for flowchart in self:
            for node in flowchart.nodes.copy().values():
                if isinstance(node, LMS_BranchNode):
                    for case, branch in node.branches.items():
                        if is_valid_jump(branch):
                            branch.next_flowchart = None
                    continue

                if is_valid_jump(node):
                    node.next_flowchart = None

    def _generate_next_id(self) -> int:
        """
        Lazy generation for the next ID of a node. IDs are normalized properly when the msbf file is being written.
        """
        next_id = self._global_node_id
        self._global_node_id += 1
        return next_id
