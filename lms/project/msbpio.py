"""
IO interface for ``MSBP`` files.
"""

import os
from typing import BinaryIO, Any

from lms.common import lms_exceptions
from lms.common.field.lms_datatype import LMS_DataType
from lms.common.stream.fileinfo import read_file_info, write_file_info, write_file_size
from lms.common.stream.hashtable import read_labels, write_labels
from lms.common.stream.section import read_section_data, write_section
from lms.fileio.io import FileReader, FileWriter
from lms.project.msbp import MSBP, MSBPSection
from lms.project.section.ali2 import read_ali2, write_ali2
from lms.project.section.ati2 import read_ati2, write_ati2
from lms.project.section.clr1 import read_clr1, write_clr1
from lms.project.section.string import read_strings, write_strings
from lms.project.section.syl3 import read_syl3, write_syl3
from lms.project.section.tag2 import read_tag2, write_tag2
from lms.project.section.tgg2 import read_tgg2, write_tgg2
from lms.project.section.tgp2 import read_tgp2, write_tgp2

__all__ = ("read_msbp", "read_msbp_path")


def read_msbp_path(file_path: str | os.PathLike[str]) -> MSBP:
    """
    Reads and retrieves a MSBP file from a given path.

    :param file_path: the path to the MSBP file.

    =====
    Usage
    =====
    >>> msbp = read_msbp_path("path/to/file.msbp")
    """
    with open(file_path, "rb") as stream:
        msbp = read_msbp(stream)
        msbp.name = os.path.basename(file_path).removesuffix(".msbp")

    return msbp




def read_msbp(stream: BinaryIO | bytes) -> MSBP:
    """
    Reads and retrieves a MSBP file from a specified stream.

    :param stream: an ``IOBase``, ``BytesIO``, ``memoryview``, or ``bytes`` object.

    =====
    Usage
    =====
    >>> msbp = read_msbp(stream)
    """
    reader = FileReader(stream)

    file_info = read_file_info(reader, MSBP.MAGIC)

    colors = None
    attr_definitions = None
    attribute_enums = None
    tag_groups = None
    tag_definitions = None
    tag_param_definitions = None
    tag_enums = None
    styles = None
    source_list = None

    last_read: tuple[Any] = ()
    section_list = []
    for magic, _ in read_section_data(reader, file_info.section_count):
        match magic:
            case MSBPSection.CLB1 | MSBPSection.ALB1 | MSBPSection.SLB1:
                # Set the name attribute of last read item
                labels, _ = read_labels(reader)
                for i in labels:
                    last_read[i].name = labels[i]
            case MSBPSection.CLR1:
                colors = read_clr1(reader)
                last_read = colors
            case MSBPSection.ATI2:
                attr_definitions = read_ati2(reader)
                last_read = attr_definitions
            case MSBPSection.ALI2:
                attribute_enums = read_ali2(reader)
            case MSBPSection.TGG2:
                tag_groups = read_tgg2(reader, file_info.version)
            case MSBPSection.TAG2:
                tag_definitions = read_tag2(reader)
            case MSBPSection.TGP2:
                tag_param_definitions = read_tgp2(reader)
            case MSBPSection.TGL2:
                tag_enums = read_strings(reader, False)
            case MSBPSection.SYL3:
                styles = read_syl3(reader)
                last_read = styles
            case MSBPSection.CTI1:
                source_list = read_strings(reader, True)
            case _:
                raise ValueError(f"Unknown section magic '{magic}' in MSBP file.")

        section_list.append(magic)

    if attr_definitions is not None:
        for definition in attr_definitions:
            if definition.datatype is not LMS_DataType.ENUM:
                continue

            definition.set_enum_members(attribute_enums)

    if tag_groups is not None:
        for group in tag_groups:
            group.set_all_definitions(tag_definitions, tag_param_definitions, tag_enums)

    return MSBP(file_info, section_list, colors, attr_definitions, tag_groups, styles, source_list)

def write_msbp_path(file_path: str | os.PathLike[str], file: MSBP) -> None:
    """
    Writes a MSBP file to a given file path. If the target path does not exist, it will be created.

    :param file_path: the path to write the file to.
    :param file: the MSBP file object.

    =====
    Usage
    =====
    >>> write_msbp_path("path/to/file.msbp", msbp)
    """
    with open(file_path, "wb") as stream:
        data = write_msbp(file)
        stream.write(data)


def write_msbp(file: MSBP) -> bytes:
    if not isinstance(file, MSBP):
        raise lms_exceptions.LMS_Error(
            f"File provided is not valid. Expected MSBP got {type(file)}."
        )

    writer = FileWriter(file.info.encoding)
    write_file_info(writer, MSBP.MAGIC, file.info)

    for section in file.section_list:
        match section:
            case MSBPSection.CLB1 | MSBPSection.ALB1 | MSBPSection.SLB1:
                labels = [item.name for item in {"CLB1":
                        file.colors, "ALB1": file.attribute_definitions, "SLB1": file.styles}[section]]
                write_section(writer, section, write_labels, labels, file.slot_count)
            case MSBPSection.CLR1:
                write_section(writer, section, write_clr1, file.colors)
            case MSBPSection.ATI2:
                write_section(writer, section, write_ati2, file.attribute_definitions)
            case MSBPSection.ALI2:
                enum_members = [definition.enum_members for definition in file.attribute_definitions if definition.datatype is LMS_DataType.ENUM]
                write_section(writer, section, write_ali2, enum_members)
            case MSBPSection.TGG2:
                write_section(writer, section, write_tgg2, file.tag_groups, file.info.version)
            case MSBPSection.TAG2:
                tag_definitions = [tag for group in file.tag_groups for tag in group.tag_definitions]
                write_section(writer, section, write_tag2, tag_definitions)
            case MSBPSection.TGP2:
                tag_parameters = [param for tag in tag_definitions for param in tag.parameters]
                write_section(writer, section, write_tgp2, tag_parameters)
            case MSBPSection.TGL2:
                enum_parameters = [param for param in tag_parameters if param.datatype is LMS_DataType.ENUM]
                enums = [member for param in enum_parameters for member in param.enum_members.values()]
                write_section(writer, section, write_strings, enums, False)
            case MSBPSection.SYL3:
                write_section(writer, section, write_syl3, file.styles)
            case MSBPSection.CTI1:
                write_section(writer, section, write_strings, file.source_files, True)

    write_file_size(writer)
    return writer.get_data()