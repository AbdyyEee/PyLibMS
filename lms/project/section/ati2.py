from lms.common.field.lms_datatype import LMS_DataType
from lms.fileio.io import FileReader
from lms.project.definitions.attribute import LMS_AttributeDefinition


def read_ati2(reader: FileReader) -> tuple[LMS_AttributeDefinition, ...]:
    definitions = []
    count = reader.read_uint32()
    for _ in range(count):
        datatype = LMS_DataType(reader.read_uint8())
        reader.skip(1)

        enum_index = reader.read_uint16()
        offset = reader.read_uint32()
        definitions.append(LMS_AttributeDefinition(datatype, offset, enum_index))

    return tuple(definitions)
