from lms.common.field.lms_datatype import LMS_DataType
from lms.fileio.io import FileReader, FileWriter
from lms.project.definitions.tag import LMS_TagParamDefinition


def read_tgp2(reader: FileReader) -> tuple[LMS_TagParamDefinition, ...]:
    param_definitions = []

    count = reader.read_uint16()
    reader.skip(2)
    for offset in reader.read_offset_array(count):
        reader.seek(offset)

        datatype = LMS_DataType(reader.read_uint8())

        if datatype is not LMS_DataType.ENUM:
            name = reader.read_encoded_string()
            param_definitions.append(LMS_TagParamDefinition(name, datatype))
            continue

        reader.skip(1)
        list_count = reader.read_uint16()
        list_indexes = reader.read_uint16_array(list_count)
        name = reader.read_encoded_string()
        param_definitions.append(
            LMS_TagParamDefinition(name, LMS_DataType.ENUM, list_indexes)
        )
        reader.align(4)

    return tuple(param_definitions)


def write_tgp2(writer: FileWriter, parameters: list[LMS_TagParamDefinition]) -> None:
    data_start = writer.tell()
    writer.write_uint16(len(parameters))
    writer.write_bytes(b"\x00" * len(parameters) * 4)

    offset = 4 * len(parameters) + 4

    writer.seek(data_start + 4)
    for i, param in enumerate(parameters):
        writer.seek(data_start + 4 + (4 * i))
        writer.write_uint32(offset)
        writer.seek(data_start + offset)

        writer.write_uint8(param.datatype)
        offset += 1

        if param.datatype is LMS_DataType.ENUM:
            writer.write_bytes(b"\x00")
            writer.write_uint16(len(param.enum_members))
            writer.write_uint16_array(param.enum_indices)
            offset += (
                3
                + 2 * len(param.enum_members)
                + writer.write_encoded_string(param.name)
            )
        else:
            offset += writer.write_encoded_string(param.name)

        offset += writer.write_alignment(b"\x00", 4)
