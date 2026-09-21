"""
IO interface for ``MSBT`` files.
"""

from typing import BinaryIO, overload

from lms.common import lms_exceptions
from lms.common.stream.fileinfo import read_file_info, write_file_info, write_file_size
from lms.common.stream.hashtable import read_labels, write_labels
from lms.common.stream.section import (
    read_section_data,
    write_section,
    write_unsupported_section,
)
from lms.fileio.io import FileReader, FileWriter
from lms.message.msbt import MSBT
from lms.message.msbtentry import MSBTEntry
from lms.message.section.atr1 import read_atr1, write_decoded_atr1, write_encoded_atr1
from lms.message.section.nli1 import read_nli1, write_nli1
from lms.message.section.tsy1 import read_tsy1, write_tsy1
from lms.message.section.txt2 import read_txt2, write_txt2
from lms.titleconfig.config import AttributeConfig, TagConfig

__all__ = ("read_msbt", "read_msbt_path", "write_msbt", "write_msbt_path")


@overload
def read_msbt_path(file_path: str, attribute_config: AttributeConfig) -> MSBT: ...


def read_msbt_path(
    file_path: str,
    *,
    attribute_config: AttributeConfig | None = None,
    tag_config: TagConfig | None = None,
    suppress_tag_errors: bool = False,
) -> MSBT:
    """
    Reads and retrieves a MSBT file from a given path.

    :param file_path: the path to the MSBT file.
    :param attribute_config: the attribute config to use for decoding attributes.
    :param tag_config: the tag config to use for decoding tags.
    :param suppress_tag_errors: when a tag config is used, suppress any errors while reading decoded tags.

    =====
    Usage
    =====
    >>> msbt = read_msbt_path("path/to/file.msbt")
    """
    with open(file_path, "rb") as stream:
        return read_msbt(
            stream,
            attribute_config=attribute_config,
            tag_config=tag_config,
            suppress_tag_errors=suppress_tag_errors,
        )


def read_msbt(
    stream: BinaryIO | bytes,
    *,
    attribute_config: AttributeConfig | None = None,
    tag_config: TagConfig | None = None,
    suppress_tag_errors: bool = False,
) -> MSBT:
    """
    Reads and retrieves a MSBT file from a specified stream.

    :param stream: an ``IOBase``, ``BytesIO``, ``memoryview``, or ``bytes`` object.
    :param attribute_config: the attribute config to use for decoding attributes.
    :param tag_config: the tag config to use for decoding tags.
    :param suppress_tag_errors: when a tag config is used, suppress any errors while reading decoded tags.

    =====
    Usage
    =====
    >>> msbt = read_msbt(stream)
    """
    reader = FileReader(stream)
    file_info = read_file_info(reader, MSBT.MAGIC)

    section_list = []
    unsupported_sections = {}

    # While 101 is the default slot count for LBL1 sections in a MSBT
    # The value may be overridden at the instance level... not sure why it varies though...
    slot_count = MSBT.DEFAULT_SLOT_COUNT

    messages = atr1_data = style_indices = None

    labels: dict[int, str] = {}
    uses_nli1 = False
    for magic, size in read_section_data(reader, file_info.section_count):
        match magic:
            case "LBL1":
                labels, slot_count = read_labels(reader)
            case "NLI1":
                labels = read_nli1(reader)
                uses_nli1 = True
            case "ATR1":
                atr1_data = read_atr1(reader, attribute_config, size)
            case "TXT2":
                messages = read_txt2(reader, tag_config, suppress_tag_errors)
            case "TSY1":
                style_indices = read_tsy1(reader, len(labels))
            case _:
                unsupported_sections[magic] = reader.read_bytes(size)

        if magic not in section_list:
            section_list.append(magic)

    file = MSBT(
        file_info,
        uses_nli1,
        section_list,
        unsupported_sections,
        attribute_config,
        tag_config,
    )
    file.slot_count = slot_count

    file.uses_encoded_attributes = attribute_config is None
    if atr1_data is not None:
        file.size_per_attribute = atr1_data.size_per_attribute
        file.attr_string_table = atr1_data.string_table

    for i, label in labels.items():
        text = None if messages is None else messages[i]
        attr = None if atr1_data is None else atr1_data.attributes[i]
        style = None if style_indices is None else style_indices[i]
        file.add_entry(
            MSBTEntry(label, message=text, attribute=attr, style_index=style)
        )

    return file


def write_msbt_path(file_path: str, file: MSBT) -> None:
    """
    Writes a MSBT file to a given file path. If the target path does not exist, it will be created.

    :param file_path: the path to write the file to.
    :param file: the MSBT file object.

    =====
    Usage
    =====
    >>> write_msbt_path("path/to/file.msbt", msbt)
    """
    with open(file_path, "wb") as stream:
        data = write_msbt(file)
        stream.write(data)


def write_msbt(file: MSBT) -> bytes:
    """Writes a MSBT file and returns the data.

    :param file: a MSBT object.

    =====
    Usage
    =====
    >>> data = write_msbt(msbt)
    """
    if not isinstance(file, MSBT):
        raise lms_exceptions.LMS_Error(
            f"File provided is not valid. Expected MSBT got {type(file)}."
        )

    writer = FileWriter(file.info.encoding)
    write_file_info(writer, MSBT.MAGIC, file.info)

    for section in file.section_list:
        match section:
            case "LBL1":
                labels = [entry.name for entry in file]
                write_section(writer, "LBL1", write_labels, labels, file.slot_count)
            case "NLI1":
                labels = [entry.name for entry in file]
                write_section(writer, "NLI1", write_nli1, labels)
            case "ATR1":
                attributes = [entry.attribute for entry in file]
                if file.uses_encoded_attributes:
                    write_section(
                        writer,
                        "ATR1",
                        write_encoded_atr1,
                        attributes,
                        file.size_per_attribute,
                        file.attr_string_table,
                    )
                else:
                    write_section(
                        writer,
                        "ATR1",
                        write_decoded_atr1,
                        attributes,
                        file.size_per_attribute,
                    )
            case "TXT2":
                messages = [entry.message for entry in file]
                write_section(writer, "TXT2", write_txt2, messages)
            case "TSY1":
                style_indexes = [entry.style_index for entry in file]
                write_section(writer, "TSY1", write_tsy1, style_indexes)
            case _:
                write_unsupported_section(
                    writer, section, file.get_unsupported_section_data(section)
                )

    write_file_size(writer)
    return writer.get_data()
