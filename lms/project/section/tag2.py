from lms.fileio.io import FileReader
from lms.project.definitions.tag import LMS_TagDefinition


def read_tag2(reader: FileReader) -> list[LMS_TagDefinition]:
    info_list = []

    count = reader.read_uint16()
    reader.skip(2)
    for offset in reader.read_offset_array(count):
        reader.seek(offset)

        param_count = reader.read_uint16()
        parameter_indices = reader.read_uint16_array(param_count)
        name = reader.read_encoded_string()

        info_list.append(LMS_TagDefinition(name, parameter_indices))
        reader.align(4)

    return info_list
