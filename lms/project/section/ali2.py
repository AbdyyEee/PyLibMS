from types import MappingProxyType
from typing import Mapping

from lms.fileio.io import FileReader


def read_ali2(reader: FileReader) -> list[Mapping[int, str]]:
    attr_lists = []

    count = reader.read_uint32()
    for offset in reader.read_offset_array(count):
        reader.seek(offset)

        enum = {}
        member_count = reader.read_uint32()
        for i, enum_offset in enumerate(reader.read_offset_array(member_count)):
            reader.seek(enum_offset)
            enum[i] = reader.read_encoded_string()

        attr_lists.append(MappingProxyType(enum))

    return attr_lists
