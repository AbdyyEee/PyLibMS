from lms.common.field.lms_datatype import LMS_DataType
from lms.fileio.io import FileReader
from lms.project.definitions.tag import LMS_TagParamDefinition


def read_tgp2(reader: FileReader) -> list[LMS_TagParamDefinition]:
    parameter_info = []

    count = reader.read_uint16()
    reader.skip(2)
    for offset in reader.read_offset_array(count):
        reader.seek(offset)

        datatype = LMS_DataType(reader.read_uint8())

        if datatype is not LMS_DataType.LIST:
            name = reader.read_encoded_string()
            parameter_info.append(LMS_TagParamDefinition(name, datatype))
            continue

        reader.skip(1)
        list_count = reader.read_uint16()
        list_indexes = reader.read_uint16_array(list_count)
        name = reader.read_encoded_string()
        parameter_info.append(
            LMS_TagParamDefinition(name, LMS_DataType.LIST, list_indexes)
        )
        reader.align(4)

    return parameter_info
