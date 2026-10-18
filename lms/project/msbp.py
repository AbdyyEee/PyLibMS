from enum import StrEnum

from lms.common.lms_fileinfo import LMS_FileInfo
from lms.project.definitions.attribute import LMS_AttrDefinition
from lms.project.definitions.color import LMS_Color
from lms.project.definitions.style import LMS_Style
from lms.project.definitions.tag import LMS_TagGroup
from lms.titleconfig.definitions.project import MessageSource


class MSBPSection(StrEnum):
    CLR1 = "CLR1"
    CLB1 = "CLB1"
    ATI2 = "ATI2"
    ALB1 = "ALB1"
    ALI2 = "ALI2"
    TGG2 = "TGG2"
    TAG2 = "TAG2"
    TGP2 = "TGP2"
    TGL2 = "TGL2"
    SYL3 = "SYL3"
    SLB1 = "SLB1"
    CTI1 = "CTI1"

class MSBP:
    """
    A class that represents a MSBP file.
    """

    MAGIC = "MsgPrjBn"
    DEFAULT_SLOT_COUNT = 0x1D

    def __init__(
            self,
            info: LMS_FileInfo,
            section_list: list[str] | None,
            colors: list[LMS_Color],
            config: tuple[LMS_AttrDefinition],
            tag_groups: tuple[LMS_TagGroup],
            styles: list[LMS_Style],
            source_files: list[str],
    ):
        self.name = ""
        self.slot_count = self.DEFAULT_SLOT_COUNT

        self._info = info
        self._section_list = section_list
        self._colors = colors
        self._attribute_definitions = config
        self._tag_groups = tag_groups
        self._styles = styles
        self._source_files = source_files

    @property
    def info(self) -> LMS_FileInfo:
        """The file info for the MSBP instance."""
        return self._info

    @property
    def section_list(self) -> tuple[str, ...]:
        """List of sections in the MSBP file."""
        return tuple(self._section_list)

    @property
    def colors(self) -> tuple[LMS_Color, ...]:
        """The color definitions for the project."""
        return tuple(self._colors)

    @property
    def attribute_definitions(self) -> tuple[LMS_AttrDefinition, ...]:
        """The attribute definitions for the project instance."""
        return self._attribute_definitions

    @property
    def tag_groups(self) -> tuple[LMS_TagGroup, ...]:
        """The tag group definitions for the project instance."""
        return self._tag_groups

    @property
    def styles(self) -> tuple[LMS_Style, ...]:
        """The style definitions for the project instance."""
        return tuple(self._styles)

    @property
    def source_files(self) -> tuple[str, ...]:
        """The source file definitions for the project instance."""
        return tuple(self._source_files)

    def add_color(self, color: LMS_Color) -> None:
        """
        Add a color to the MSBP instance.

        :param color: The color to add.
        """
        self._colors.append(color)

    def add_style(self, style: LMS_Style) -> None:
        """
        Add a color to the MSBP instance.

        :param style: The style to add.
        """
        self._styles.append(style)

    def add_source(self, source: MessageSource) -> None:
        """
        Add a source to the MSBP instance.

        New files that are referenced in any MSBF flowcharts (e.g. Message nodes, Jump Nodes to external flowcharts),
        must  have their source file added to the MSBP.

        :param source: The source to add, a custom file. If an LMS format, should end in ``.mstxt`` or ``.msflow``
        """
        self._source_files.append(source)
