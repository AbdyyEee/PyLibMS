import os
from typing import BinaryIO

from lms.common.field.lms_datatype import LMS_DataType
from lms.common.stream.fileinfo import read_file_info
from lms.common.stream.hashtable import read_labels
from lms.common.stream.section import read_section_data
from lms.fileio.io import FileReader
from lms.project.msbp import MSBP
from lms.project.section.ali2 import read_ali2
from lms.project.section.ati2 import read_ati2
from lms.project.section.clr1 import read_clr1
from lms.project.section.string import read_strings
from lms.project.section.syl3 import read_styles
from lms.project.section.tag2 import read_tag2
from lms.project.section.tgg2 import read_tgg2
from lms.project.section.tgp2 import read_tgp2

__all__ = ("read_msbp", "read_msbp_path")


def read_msbp_path(file_path: str) -> MSBP:
    """
    Reads and retrieves a MSBP file from a given path.

    :param file_path: the path to the MSBP file.

    =====
    Usage
    =====
    >>> msbp = read_msbp_path("path/to/file.msbp")
    """
    with open(file_path, "rb") as stream:
        return read_msbp(stream)


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
    attribute_list_items = None
    tag_groups = None
    tag_definitions = None
    tag_param_definitions = None
    tag_list_items = None
    styles = None
    source_list = None

    items = []
    for magic, _ in read_section_data(reader, file_info.section_count):
        match magic:
            case "CLB1" | "ALB1" | "SLB1":
                # Set the name attribute of last read item
                labels, _ = read_labels(reader)
                for i in labels:
                    items[i].name = labels[i]
            case "CLR1":
                colors = read_clr1(reader)
                items = colors
            case "ATI2":
                attr_definitions = read_ati2(reader)
                items = attr_definitions
            case "ALI2":
                attribute_list_items = read_ali2(reader)
            case "TGG2":
                tag_groups = read_tgg2(reader, file_info.version)
            case "TAG2":
                tag_definitions = read_tag2(reader)
            case "TGP2":
                tag_param_definitions = read_tgp2(reader)
            case "TGL2":
                tag_list_items = read_strings(reader, False)
            case "SYL3":
                styles = read_styles(reader)
                items = styles
            case "CTI1":
                source_list = read_strings(reader, True)
            case _:
                raise ValueError(f"Unknown section magic '{magic}' in MSBP file.")

    if attr_definitions is not None:
        for definition in attr_definitions:
            if definition.datatype is LMS_DataType.LIST:
                definition.list_items = attribute_list_items[definition.list_index]

    if tag_groups is not None:
        for group in tag_groups:
            group.set_all_definitions(
                tag_definitions, tag_param_definitions, tag_list_items
            )

    file = MSBP(file_info, colors, attr_definitions, tag_groups, styles, source_list)

    if isinstance(stream, BinaryIO):
        file.name = os.path.basename(stream.name).removesuffix(".msbp")

    return file
