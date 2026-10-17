from types import MappingProxyType
from typing import Mapping

from lms.fileio.io import FileReader, FileWriter


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

def write_ali2(writer: FileWriter, attribute_enums: list[Mapping[int, str]]) -> None:
    data_start = writer.tell()
    writer.write_uint32(len(attribute_enums))
    writer.write_bytes(b"\x00" *  (4 + len(attribute_enums) * 4))

    offset = 4 * len(attribute_enums) + 4

    writer.seek(data_start + 4)
    for i, enum in enumerate(attribute_enums):
        writer.seek(data_start + 4 + (4 * i))
        writer.write_uint32(offset)
        writer.seek(offset + data_start)

        enum_start = writer.tell()

        writer.write_uint32(len(enum))
        writer.write_bytes(b"\x00" * (len(enum) * 4))
        offset += 4 + len(enum) * 4

        enum_offset = 4 * len(enum) + 4
        writer.seek(enum_start + 4)

        for enum_i, member in enum.items():
            writer.seek((enum_start + 4) + 4 * enum_i)
            writer.write_uint32(enum_offset)
            writer.seek(enum_start + enum_offset)
            member_length = writer.write_encoded_string(member)

            enum_offset += member_length
            offset += member_length

        offset += writer.write_alignment(b"\x00", 4)










