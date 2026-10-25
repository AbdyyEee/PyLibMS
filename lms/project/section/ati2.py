from lms.common.field.lms_datatype import LMS_DataType
from lms.fileio.io import FileReader, FileWriter
from lms.project.definitions.attribute import LMS_AttrDefinition


def read_ati2(reader: FileReader) -> tuple[LMS_AttrDefinition, ...]:
    definitions = []
    count = reader.read_uint32()
    for _ in range(count):
        datatype = LMS_DataType(reader.read_uint8())
        reader.skip(1)

        enum_index = reader.read_uint16()
        offset = reader.read_uint32()
        definitions.append(LMS_AttrDefinition(datatype, offset, enum_index))

    return tuple(definitions)


def write_ati2(writer: FileWriter, definitions: tuple[LMS_AttrDefinition, ...]) -> None:
    writer.write_uint32(len(definitions))

    for definition in definitions:
        writer.write_uint8(definition.datatype)
        writer.write_bytes(b"\x00")
        writer.write_uint16(definition.enum_index)
        writer.write_uint32(definition.offset)
