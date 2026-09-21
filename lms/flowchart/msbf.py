from types import MappingProxyType

from lms.common.lms_fileinfo import LMS_FileInfo
from lms.fileio.encoding import FileEncoding
from lms.flowchart.definitions.flowchart import LMS_Flowchart
from lms.flowchart.definitions.node import LMS_EntryNode


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

    def set_global_id_count(self, value: int) -> None:
        self._global_node_id = value

    def generate_next_id(self) -> int:
        """
        Lazy generation for the next ID of a node. IDs are normalized properly when the msbf file is being written.
        """
        next_id = self._global_node_id
        self._global_node_id += 1
        return next_id

    def add_flowchart(
        self, flowchart_name: str, entry_point: LMS_EntryNode | None = None
    ) -> LMS_Flowchart:
        """
        Add a flowchart to the MSBF instance.

        :param flowchart_name: The name of the new flowchart.
        """
        if flowchart_name in self.flowcharts:
            raise KeyError(f"Flowchart with name '{flowchart_name}' already exists!")

        if entry_point is None:
            entry_point = LMS_EntryNode(
                self.generate_next_id(), flowchart_name=flowchart_name
            )

        flowchart = LMS_Flowchart(entry_point, self.generate_next_id)
        self._flowcharts.append(flowchart)
        return flowchart

    def delete_flowchart(self, name: str):
        """Delete a flowchart from the MSBF instance."""

        if name not in self.flowcharts:
            raise KeyError(f"Flowchart with name {name} does not exist!")

        del self._flowcharts[name]
