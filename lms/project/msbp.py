from lms.common.lms_fileinfo import LMS_FileInfo
from lms.project.definitions.attribute import LMS_AttributeDefinition
from lms.project.definitions.color import LMS_Color
from lms.project.definitions.style import LMS_Style
from lms.project.definitions.tag import LMS_TagGroup


class MSBP:
    """
    A class that represents a MSBP file.

    ======
    Usages
    ======
    https://github.com/AbdyyEee/PylibMS/wiki/MSBP

    =========
    File Info
    =========
    https://nintendo-formats.com/libs/lms/msbp.html
    """

    MAGIC = "MsgPrjBn"

    def __init__(
        self,
        info: LMS_FileInfo,
        colors: list[LMS_Color] | None,
        config: list[LMS_AttributeDefinition] | None,
        tag_groups: list[LMS_TagGroup] | None,
        styles: list[LMS_Style] | None,
        source_files: list[str] | None,
    ):
        self.name = ""

        self._info = info
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
    def colors(self) -> list[LMS_Color] | None:
        """The color definitions for the project."""
        return self._colors

    @property
    def attribute_definitions(self) -> list[LMS_AttributeDefinition] | None:
        """The attribute definitions for the project instance."""
        return self._attribute_definitions

    @property
    def tag_groups(self) -> list[LMS_TagGroup] | None:
        """The tag group definitions for the project instance."""
        return self._tag_groups

    @property
    def style_list(self) -> list[LMS_Style] | None:
        """The style definitions for the project instance."""
        return self._styles

    @property
    def source_files(self) -> list[str] | None:
        """The source file definitions for the project instance."""
        return self._source_files
