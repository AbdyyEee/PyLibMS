"""
IO interface for ``MSBT`` files.
"""
import os
from enum import StrEnum
from types import MappingProxyType
from typing import BinaryIO, Mapping

from lms.common import lms_exceptions
from lms.common.stream.fileinfo import read_file_info, write_file_info, write_file_size
from lms.common.stream.hashtable import read_labels, write_labels
from lms.common.stream.section import (
    read_section_data,
    write_section,
    write_unsupported_section,
)
from lms.fileio.io import FileReader, FileWriter
from lms.message.msbt import MSBT, MSBTSection
from lms.message.msbtentry import MSBTEntry
from lms.message.section.ato1 import read_ato1, write_ato1
from lms.message.section.atr1 import read_atr1, write_decoded_atr1, write_encoded_atr1
from lms.message.section.nli1 import read_nli1, write_nli1
from lms.message.section.tsy1 import read_tsy1, write_tsy1
from lms.message.section.txt2 import read_txt2, write_txt2
from lms.titleconfig.config import TagConfig

__all__ = ("read_msbt_path", "read_msbt_directory", "read_msbt", "write_msbt", "write_msbt_path")

from lms.titleconfig.definitions.project import Project

MSBT_EXTENSION = ".msbt"

def read_msbt_path(
        file_path: str | os.PathLike[str],
        *,
        project: Project | None = None,
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
        msbt = read_msbt(
            stream,
            project=project,
            suppress_tag_errors=suppress_tag_errors,
        )
        msbt.filename = os.path.basename(file_path)

    return msbt


def read_msbt_directory(directory: str | os.PathLike[str], *,
                        project: Project | None = None,
                        suppress_tag_errors: bool = False,
                        ignore_extensions: bool = False) -> Mapping[str, MSBT]:
    """
    Reads and retrieves all MSBT files from a given directory.

    :param directory: directory of MSBT files. All files must have the `.msbt` extension (unless ``ignore_extensions``
    is True)
    :param project: a ``Project` object.
    :param suppress_tag_errors: when a tag config is used, suppress any errors while reading decoded tags.
    :param ignore_extensions: ignore the extensions in the directory.

    =====
    Usage
    =====
    >>> msbt = read_msbt_directory("path/to/directory")
    """
    files: dict[str, MSBT] = {}

    for file in os.listdir(directory):
        if not file.endswith(MSBT_EXTENSION) and not ignore_extensions:
            raise ValueError("This directory contains a non-MSBT file. "
                             "Only directories with MSBT files can be used! Set ignore_extensions to True to ignore"
                             "this error.")

        msbt = read_msbt_path(os.path.join(directory, file),
                              project=project, suppress_tag_errors=suppress_tag_errors)
        msbt.filename = file
        files[file] = msbt

    return MappingProxyType(files)




def read_msbt(
        stream: BinaryIO | bytes,
        *,
        project: Project | None = None,
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

    messages = attribute_data = style_indices = None

    labels: dict[int, str] = {}

    attribute_offsets = None
    for magic, size in read_section_data(reader, file_info.section_count):
        match magic:
            case MSBTSection.LBL1:
                labels, slot_count = read_labels(reader)
            case MSBTSection.NLI1:
                labels = read_nli1(reader)
            case MSBTSection.ATO1:
                attribute_offsets = read_ato1(reader, size)
            case MSBTSection.ATR1:
                attribute_data = read_atr1(reader, attribute_offsets, None if project is None else project.attributes, size)
            case MSBTSection.TXT2:
                messages = read_txt2(reader, None if project is None else project.tag_config, suppress_tag_errors)
            case MSBTSection.TSY1:
                style_indices = read_tsy1(reader, len(labels))
            case _:
                unsupported_sections[magic] = reader.read_bytes(size)

        if magic not in section_list:
            section_list.append(magic)

    file = MSBT(
        file_info,
        section_list,
        unsupported_sections,
        attribute_offsets,
        project,
    )
    file.slot_count = slot_count


    if attribute_data is not None:
        file.size_per_attribute = attribute_data.size_per_attribute
        file.attr_string_table = attribute_data.string_table

    for i, label in labels.items():
        text = None if messages is None else messages[i]
        attr = None if attribute_data is None else attribute_data.attributes[i]
        style = None if style_indices is None else style_indices[i]
        file.create_entry(label, message=text, attribute=attr, style_index=style, project=project)
    return file


def write_msbt_path(file_path: str | os.PathLike[str], file: MSBT) -> None:
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
            case MSBTSection.LBL1:
                labels = [entry.name for entry in file]
                write_section(writer, section, write_labels, labels, file.slot_count)
            case MSBTSection.NLI1:
                labels = [entry.name for entry in file]
                write_section(writer, section, write_nli1, labels)
            case MSBTSection.ATO1:
                write_section(writer, section, write_ato1, file.attribute_offsets)
            case MSBTSection.ATR1:
                attributes = [entry.attribute for entry in file]
                if file.uses_encoded_attributes:
                    write_section(
                        writer,
                        section,
                        write_encoded_atr1,
                        attributes,
                        file.size_per_attribute,
                        file.attr_string_table,
                    )
                else:
                    write_section(
                        writer,
                        section,
                        write_decoded_atr1,
                        attributes,
                        file.size_per_attribute,
                    )
            case MSBTSection.TXT2:
                messages = [entry.message for entry in file]
                write_section(writer, section, write_txt2, messages)
            case MSBTSection.TSY1:
                style_indexes = [entry.style_index for entry in file]
                write_section(writer, "TSY1", write_tsy1, style_indexes)
            case _:
                write_unsupported_section(
                    writer, section, file.get_unsupported_section_data(section)
                )

    write_file_size(writer)
    return writer.get_data()
