import json
from enum import StrEnum
from types import MappingProxyType
from typing import overload, Mapping, Iterator, Self, Any

import yaml

from lms.common.field.lms_field import LMS_FieldMap
from lms.common.lms_constants import LMS_MINIMUM_VERSION, DEFAULT_SECTION_COUNT
from lms.common.lms_fileinfo import LMS_FileInfo
from lms.fileio.encoding import FileEncoding
from lms.fileio.endian import FileEndian
from lms.message.lms_messagetext import LMS_MessageText
from lms.message.msbtentry import MSBTEntry
from lms.message.section.atr1 import NO_OFFSET
from lms.titleconfig.definitions.project import Project


class MSBTSection(StrEnum):
    LBL1 = "LBL1"
    NLI1 = "NLI1"
    ATO1 = "ATO1"
    ATR1 = "ATR1"
    TXT2 = "TXT2"
    TSY1 = "TSY1"


class MSBT:
    """
    A class that represents a MSBT file.
    """

    MAGIC = "MsgStdBn"

    DEFAULT_SLOT_COUNT = 0x65

    ATR1_INDEX = 0x1
    TXT2_INDEX = 0x2
    TSY1_INDEX = 0x3

    def __init__(
        self,
        info: LMS_FileInfo | None = None,
        section_list: list[str] = None,
        unsupported_section_map: dict[str, bytes] | None = None,
        attribute_offsets: list[int] | None = None,
        project: Project | None = None,
    ):
        self._info = info if info is not None else LMS_FileInfo()

        self._entries: list[MSBTEntry] = []
        self._label_map: dict[str, MSBTEntry] = {}

        self.size_per_attribute = 0
        self.slot_count = MSBT.DEFAULT_SLOT_COUNT

        self.attr_string_table: bytes | None = None
        self._attribute_offsets = attribute_offsets

        self._unsupported_section_map = unsupported_section_map or {}

        # Store the section list so that the order of any and all sections is preserved when writing
        self._section_list = section_list

        self._project = project

    @overload
    def __getitem__(self, index: int) -> MSBTEntry: ...

    @overload
    def __getitem__(self, label: str) -> MSBTEntry: ...

    def __getitem__(self, value: int | str) -> MSBTEntry:
        if isinstance(value, str):
            return self._label_map[value]

        return self._entries[value]

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[MSBTEntry]:
        return iter(self._entries)

    @classmethod
    def new(
        cls,
        uses_nli1: bool = False,
        project: Project | None = None,
        endian: FileEndian = FileEndian.LITTLE,
        encoding: FileEncoding = FileEncoding.UTF16,
        version: int = LMS_MINIMUM_VERSION,
        section_count: int = DEFAULT_SECTION_COUNT,
    ):
        """
        Create a new MSBT instance.

        :param uses_nli1: flag to determine if to use nli1 section for labels.
        :param project: specific project from a config.
        :param endian: if the file is big endian.
        :param encoding: the file encoding.
        :param version: the file version.
        :param section_count: the number of sections.
        """
        return MSBT(
            LMS_FileInfo(endian, encoding, version, section_count),
            section_list=[
                MSBTSection.LBL1 if not uses_nli1 else MSBTSection.NLI1,
                MSBTSection.TXT2,
            ],
            project=project,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any], project: Project = None) -> Self:
        """
        Instantiates a new MSBT object from a dictionary.

        :param data: the dictionary to parse.
        :param project: the project from a config.
        """
        endian = FileEndian(data["endian"])
        encoding = FileEncoding(data["encoding"])
        version = data["version"]
        section_count = data["section_count"]

        msbt = cls(
            LMS_FileInfo(endian, encoding, version, section_count),
            data["section_list"],
            attribute_offsets=data.get("attribute_offsets"),
            project=project,
        )

        for name, entry in data["entries"].items():
            message = LMS_MessageText(
                entry["message"], None if project is None else project.tag_config
            )

            if (attribute := entry.get("attribute")) is not None:
                if isinstance(attribute, str):
                    attr = bytes.fromhex(attribute)
                else:
                    attr = LMS_FieldMap.from_dict(attribute, project.attributes)

            msbt.create_entry(
                name,
                message=message,
                attribute=attr,
                style_index=entry.get("style_index"),
            )

        msbt.slot_count = data["slot_count"]
        return msbt

    @classmethod
    def from_json(cls, data: str, project: Project = None) -> Self:
        """
        Instantiates a new MSBT object from a JSON string.

        :param data: the string to parse.
        :param project: the project from a config.
        """
        return cls.from_dict(json.loads(data), project=project)

    @classmethod
    def from_yaml(cls, data: str, project: Project = None) -> Self:
        """
        Instantiates a new MSBT object from a YAML string.

        :param data: the string to parse.
        :param project: the project from a config.
        """
        return cls.from_dict(yaml.loads(data), project=project)

    def to_dict(self) -> dict:
        """Convert the MSBT object to a dictionary."""
        data = {
            "filename": self.filename,
            "info": self.info.to_dict(),
            "slot_count": self.slot_count,
            "section_list": self.section_list,
        }

        if self.section_exists(MSBTSection.ATO1):
            data["attribute_offsets"] = [
                NO_OFFSET if offset is None else offset
                for offset in self._attribute_offsets
            ]

        data |= self.info.to_dict()
        entries = {}

        for entry in self:
            entries[entry.name] = entry_dict = {"message": entry.message.text}

            if self.contains_attributes and entry.attribute is not None:

                if isinstance(entry.attribute, bytes):
                    entry_dict["attribute"] = entry.attribute.hex().upper()
                else:
                    entry_dict["attribute"] = entry.attribute.to_dict()

            if self.contains_styles:
                entry_dict["style_index"] = entry.style_index

        data["entries"] = entries
        return data

    def to_json(self) -> str:
        """Convert the MSBT object to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_yaml(self) -> str:
        """Convert the MSBT object to a YAML string."""
        return yaml.safe_dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @property
    def info(self) -> LMS_FileInfo:
        """The file info for the MSBT instance."""
        return self._info

    @property
    def entries(self) -> tuple[MSBTEntry, ...]:
        """Tuple of all the MSBT entries."""
        return tuple(self._entries)

    @property
    def label_map(self) -> Mapping[str, MSBTEntry]:
        """Mapping of all labels to MSBT entries."""
        return MappingProxyType(self._label_map)

    @property
    def section_list(self) -> tuple[str, ...]:
        """The list of sections with order preserved."""
        return tuple(self._section_list)

    @property
    def unsupported_sections(self) -> tuple[str, ...]:
        """The list of unsupported sections."""
        return tuple(self._unsupported_section_map.keys())

    @property
    def attribute_offsets(self) -> tuple[str, ...] | None:
        """List of valid attribute offsets. Only valid if ATO1 is present."""
        return tuple(self._attribute_offsets)

    @property
    def contains_nli1(self) -> bool:
        """If the MSBT contains the NLI1 section."""
        return self.section_exists(MSBTSection.NLI1)

    @property
    def contains_attributes(self) -> bool:
        """If the MSBT contains attributes."""
        return self.section_exists(MSBTSection.ATR1)

    @property
    def uses_encoded_attributes(self) -> bool:
        """If the MSBT uses encoded attributes."""
        return self.section_exists("ATR1") and self._project is None

    @property
    def contains_styles(self) -> bool:
        """If the MSBT contains style indexes."""
        return self.section_exists(MSBTSection.TSY1)

    def label_exists(self, label: str) -> bool:
        """
        Returns if a label already exists in the MSBT instance.

        :param label: the label to check.
        """
        return label in self._label_map

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
            if self._entries:
                raise ValueError("All entries must have attributes tied to them!")

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

    def create_entry(
        self,
        name: str,
        *,
        message: str = None,
        attribute: LMS_FieldMap | bytes | None = None,
        style_index: int = None,
        project: Project | None = None,
    ) -> MSBTEntry:
        """
        Creates an MSBT Entry and adds it to the file.

        :param name: the name of the entry.
        :param message: the message of the entry.
        :param attribute: the attribute of the entry.
        :param style_index: the style of the entry.
        :param project: optional project, used for styles.
        """
        tag_config = None if project is None else project.tag_config
        self.add_entry(
            entry := MSBTEntry(
                name,
                message=LMS_MessageText(message, tag_config),
                attribute=attribute,
                style_index=style_index,
                project=project,
            )
        )
        return entry

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
