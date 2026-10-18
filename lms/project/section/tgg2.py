from lms.common.lms_constants import LMS_VERSION_FOUR
from lms.fileio.io import FileReader, FileWriter
from lms.project.definitions.tag import LMS_TagGroup



def read_tgg2(reader: FileReader, version: int) -> tuple[LMS_TagGroup, ...]:
    group_list = []

    count = reader.read_uint16()
    reader.skip(2)
    for i, offset in enumerate(reader.read_offset_array(count)):
        reader.seek(offset)

        group_id = reader.read_uint16() if version == LMS_VERSION_FOUR else i

        tag_count = reader.read_uint16()
        tag_indexes = reader.read_uint16_array(tag_count)

        name = reader.read_encoded_string()
        group_list.append(LMS_TagGroup(name, group_id, tag_indexes))
        reader.align(4)

    return tuple(group_list)

def write_tgg2(writer: FileWriter, groups: list[LMS_TagGroup], version: int) -> None:
    data_start = writer.tell()
    writer.write_uint16(len(groups))
    writer.write_bytes(b"\x00" *  len(groups) * 4)

    offset = 4 * len(groups) + 4
    writer.seek(data_start + 4)
    for i, group in enumerate(groups):
        writer.seek(data_start + 4 + (4 * i))
        writer.write_uint32(offset)
        writer.seek(data_start + offset)

        if version == LMS_VERSION_FOUR:
            writer.write_uint16(group.group_id)
            offset += 2

        writer.write_uint16(len(group.tag_definitions))
        writer.write_uint16_array(group.tag_indices)
        name_length = writer.write_encoded_string(group.name)
        alignment = writer.write_alignment(b"\x00", 4)
        offset += 2 + 2 * len(group.tag_definitions) + name_length + alignment




