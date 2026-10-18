from lms.fileio.io import FileReader, FileWriter
from lms.project.definitions.tag import LMS_TagDefinition


def read_tag2(reader: FileReader) -> tuple[LMS_TagDefinition]:
    definitions = []

    count = reader.read_uint16()
    reader.skip(2)
    for offset in reader.read_offset_array(count):
        reader.seek(offset)

        param_count = reader.read_uint16()
        parameter_indices = reader.read_uint16_array(param_count)
        name = reader.read_encoded_string()

        definitions.append(LMS_TagDefinition(name, parameter_indices))
        reader.align(4)

    return tuple(definitions)

def write_tag2(writer: FileWriter, tags: list[LMS_TagDefinition]) -> None:
    data_start = writer.tell()
    writer.write_uint16(len(tags))
    writer.write_bytes(b"\x00" * len(tags) * 4)

    offset = 4 * len(tags) + 4
    writer.seek(data_start + 4)
    for i, tag in enumerate(tags):
        writer.seek(data_start + 4 + (4 * i))
        writer.write_uint32(offset)
        writer.seek(data_start + offset)

        writer.write_uint16(len(tag.parameters))
        writer.write_uint16_array(tag.parameter_indices)

        name_length = writer.write_encoded_string(tag.name)
        alignment = writer.write_alignment(b"\x00", 4)
        offset += 2 + 2 * len(tag.parameters) + name_length + alignment
