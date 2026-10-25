from dataclasses import dataclass

from lms.common.field.io import read_field, write_field
from lms.common.field.lms_datatype import LMS_DataType
from lms.common.field.lms_field import LMS_Field, LMS_FieldMap
from lms.fileio.io import FileReader, FileWriter
from lms.titleconfig.definitions.attribute import AttributeDefinition

NO_OFFSET = 0xFFFF


@dataclass(frozen=True)
class AttributeData:
    attributes: list[bytes] | list[LMS_FieldMap]
    size_per_attribute: int
    string_table: bytes | None = None


def read_atr1(
    reader: FileReader,
    offsets: list[int],
    definitions: tuple[AttributeDefinition, ...] | None,
    section_size: int,
) -> AttributeData:
    return (
        read_encoded_atr1(reader, section_size)
        if definitions is None
        else read_decoded_atr1(reader, offsets, definitions)
    )


def read_encoded_atr1(reader: FileReader, section_size: int) -> AttributeData:
    absolute_size = section_size + reader.tell()

    attribute_count = reader.read_uint32()
    size_per_attribute = reader.read_uint32()

    attributes = [reader.read_bytes(size_per_attribute) for _ in range(attribute_count)]

    string_table = None
    if section_size > 8 + size_per_attribute * attribute_count:
        string_table = reader.read_bytes(absolute_size - reader.tell())

    return AttributeData(attributes, size_per_attribute, string_table)


def read_decoded_atr1(
    reader: FileReader,
    offsets: list[int | None] | None,
    definitions: tuple[AttributeDefinition, ...],
) -> AttributeData:
    section_start = reader.tell()

    attr_count = reader.read_uint32()
    size_per_attribute = reader.read_uint32()

    attributes, attr_start = [], reader.tell()

    # Map offsets to the valid definitions if ATO1 exists
    valid_definitions: dict[int, AttributeDefinition] = {}
    if offsets is not None:
        for offset, definition in zip(offsets, definitions):
            if offset is None:
                continue
            valid_definitions[offset] = definition
    else:
        valid_definitions = {
            definition.offset: definition for definition in definitions
        }

    for i in range(attr_count):
        container_start = attr_start + i * size_per_attribute
        reader.seek(container_start)

        attribute = {}
        for offset, attr in valid_definitions.items():
            reader.seek(container_start + offset)

            if attr.datatype is LMS_DataType.STRING:
                last = reader.tell() + 4
                reader.seek(section_start + reader.read_uint32())
                value = LMS_Field(reader.read_encoded_string(), attr)
                reader.seek(last)
            else:
                value = read_field(reader, attr)

            attribute[attr.name] = value

        attributes.append(LMS_FieldMap(attribute))

    return AttributeData(attributes, size_per_attribute)


def write_encoded_atr1(
    writer: FileWriter,
    attributes: list[bytes],
    size_per_attribute: int,
    string_table: bytes | None,
) -> None:
    writer.write_uint32(len(attributes))

    if attributes:
        writer.write_uint32(size_per_attribute)
    else:
        writer.write_uint32(0)

    for attr in attributes:
        writer.write_bytes(attr)

    if string_table is not None:
        writer.write_bytes(string_table)


def write_decoded_atr1(
    writer: FileWriter, attributes: list[LMS_FieldMap], size_per_attribute: int
) -> None:
    writer.write_uint32(len(attributes))
    writer.write_uint32(size_per_attribute)

    string_table = []
    string_offset = 8 + size_per_attribute * len(attributes)

    for attr in attributes:
        for field in attr:
            if field.datatype is LMS_DataType.STRING:
                field.value = str(field.value)
                string_table.append(field.value)
                writer.write_uint32(string_offset)
                string_offset += len(field.value) * writer.encoding.width + len(
                    writer.encoding.terminator
                )
            else:
                write_field(writer, field)

    for string in string_table:
        writer.write_encoded_string(string)
