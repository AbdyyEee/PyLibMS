from lms.common.lms_fileinfo import LMS_FileInfo
from lms.fileio.encoding import FileEncoding
from lms.message.msbtentry import MSBTEntry
from lms.titleconfig.definitions.attribute import AttributeConfig
from lms.titleconfig.definitions.tags import TagConfig


class MSBT:
    """
    A class that represents a MSBT file.

    ======
    Usages
    ======
    https://github.com/AbdyyEee/PylibMS/wiki/MSBT

    =========
    File Info
    =========
    https://nintendo-formats.com/libs/lms/msbt.html
    """

    MAGIC = "MsgStdBn"

    DEFAULT_SLOT_COUNT = 101

    ATR1_INDEX = 1
    TXT2_INDEX = 2
    TSY1_INDEX = 3

    def __init__(
        self,
        info: LMS_FileInfo | None = None,
        uses_nli1: bool = False,
        section_list: list[str] | None = None,
        unsupported_section_map: dict[str, bytes] | None = None,
        attribute_config: AttributeConfig | None = None,
        tag_config: TagConfig | None = None,
    ):
        self._info = info if info is not None else LMS_FileInfo()

        self._entries: list[MSBTEntry] = []
        self._label_map: dict[str, MSBTEntry] = {}

        self.size_per_attribute = 0

        self.slot_count = MSBT.DEFAULT_SLOT_COUNT

        self.uses_encoded_attributes = True
        self.attr_string_table: bytes | None = None

        self._unsupported_section_map = unsupported_section_map or {}

        # Store the section list so that the order of any and all sections is preserved when writing
        self._section_list: list[str] = section_list or [
            "LBL1" if not uses_nli1 else "NLI1"
        ]

        self._attribute_config = attribute_config
        self._tag_config = tag_config

    @classmethod
    def new(
        cls,
        uses_nli1: bool = False,
        attribute_config: AttributeConfig | None = None,
        tag_config: TagConfig | None = None,
        is_big_endian: bool = False,
        encoding: FileEncoding = FileEncoding.UTF16,
        version: int = 3,
        section_count: int = 2,
    ):
        """
        Create a new MSBT instance.

        :param uses_nli1: flag to determine if to use nli1 section for labels.
        :param attribute_config: the attribute config object
        :param tag_config: the tag config object
        :param is_big_endian: if the file is big endian.
        :param encoding: the file encoding.
        :param version: the file version.
        :param section_count: the number of sections.

        ======
        Usages
        ======
        See https://github.com/AbdyyEee/PylibMS/wiki/MSBT#creating-a-msbt
        """
        return MSBT(
            LMS_FileInfo(is_big_endian, encoding, version, section_count),
            uses_nli1=uses_nli1,
            attribute_config=attribute_config,
            tag_config=tag_config,
        )

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    @property
    def info(self) -> LMS_FileInfo:
        """The file info for the MSBT instance."""
        return self._info

    @property
    def entries(self) -> tuple[MSBTEntry, ...]:
        """Tuple of all the MSBT entries."""
        return tuple(self._entries)

    @property
    def section_list(self) -> tuple[str, ...]:
        """The list of sections with order preserved."""
        return tuple(self._section_list)

    @property
    def unsupported_sections(self) -> tuple[str, ...]:
        """The list of unsupported sections."""
        return tuple(self._unsupported_section_map.keys())

    @property
    def uses_nli1(self) -> bool:
        """If the MSBT contains the NLI1 section."""
        return self.section_exists("NLI1")

    @property
    def contains_attributes(self) -> bool:
        """If the MSBT contains attributes."""
        return self.section_exists("ATR1")

    @property
    def contains_styles(self) -> bool:
        """If the MSBT contains style indexes."""
        return self.section_exists("TSY1")

    def label_exists(self, label: str) -> bool:
        """Returns if a label already exists in the MSBT instance.

        :param label: the label to check."""
        return label in self._label_map

    def get_entry_by_index(self, index: int) -> MSBTEntry:
        """
        Retrieves an entry given its index. Supports negative indexing.

        :param index: the index of the entry.
        """
        if not (-len(self._entries) <= index < len(self._entries)):
            raise IndexError(f"The index {index} is not a valid MSBT entry!")

        return self._entries[index]

    def get_entry_by_name(self, label: str) -> MSBTEntry:
        """
        Retrieves an entry given its name.

        :param label: the label name for the entry.
        """
        if label not in self._label_map:
            raise KeyError(f"The label '{label}' does not exist!")

        return self._label_map[label]

    def add_entry(self, entry: MSBTEntry) -> None:
        """
        Adds an entry to the MSBT instance.

        :param entry: the MSBTEntry object to add.
        """
        if entry.name in self._label_map:
            raise KeyError(f"The label '{entry.name}' already exists!")

        # The implementation of ensuring section orders are maintained are done by constant indexes.
        # In most MSBT files, it goes as LBL1/NLI1 -> TXT2 -> ATR1 -> TSY1.
        # If add_entry is utilized on a new MSBT instance, then these indexes ensure the order is maintained.
        # While technically, undocumented sections (i.e. ATO1) can prefix TXT2 and other sections,
        # we do not need to account for that scenario as they aren't supported by the library

        if self.section_exists("ATR1"):
            if entry.attribute is None:
                raise ValueError(
                    f"Entry '{entry.name}' can't be added with no attributes when attributes already exist!"
                )
        elif entry.attribute is not None:
            self._section_list.insert(self.ATR1_INDEX, "ATR1")
            self._info.section_count += 1

        if not self.section_exists("TXT2"):
            self._section_list.insert(self.TXT2_INDEX, "TXT2")

        if self.section_exists("TSY1"):
            if entry.style_index is None:
                raise ValueError(
                    f"Entry '{entry.name}' can't be added with no style index when styles already exist!"
                )
        elif entry.style_index is not None:
            self._section_list.insert(self.TSY1_INDEX, "TSY1")
            self._info.section_count += 1

        self._entries.append(entry)
        self._label_map[entry.name] = entry

    def delete_entry(self, entry: MSBTEntry) -> None:
        """
        Deletes an entry from the MSBT instance.

        :param entry: the MSBTEntry object to remove.
        """
        if entry.name not in self._label_map:
            raise KeyError(f"The entry '{entry.name}' does not exist!")

        self._entries.remove(entry)
        del self._label_map[entry.name]

    def section_exists(self, name: str) -> bool:
        """
        Determines if a section exists in the MSBT instance.

        :param name: the name of the section.
        """
        return name in self._section_list

    def get_unsupported_section_data(self, name: str) -> bytes:
        """
        Retrieves the raw data of an unsupported section.

        :param name: the name of the section.
        """
        if name not in self._unsupported_section_map:
            raise KeyError(f"The section '{name}' does not exist in the MSBT!")

        return self._unsupported_section_map[name]
