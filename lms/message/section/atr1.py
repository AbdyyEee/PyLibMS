from dataclasses import dataclass

from lms.common.field.io import read_field, write_field
from lms.common.field.lms_field import LMS_DataType, LMS_Field, LMS_FieldMap
from lms.fileio.io import FileReader, FileWriter
from lms.titleconfig.definitions.attribute import AttributeConfig


@dataclass(frozen=True)
class ATR1Data:
    attributes: list[bytes] | list[LMS_FieldMap]
    size_per_attribute: int
    string_table: bytes | None


def read_atr1(
    reader: FileReader, config: AttributeConfig | None, section_size: int
) -> ATR1Data:
    if config is None:
        return read_encoded_atr1(reader, section_size)
    return read_decoded_atr1(reader, config)


def read_encoded_atr1(reader: FileReader, section_size: int) -> ATR1Data:
    absolute_size = section_size + reader.tell()

    attribute_count = reader.read_uint32()
    size_per_attribute = reader.read_uint32()

    attributes = [reader.read_bytes(size_per_attribute) for _ in range(attribute_count)]

    string_table = None
    if section_size > 8 + size_per_attribute * attribute_count:
        string_table = reader.read_bytes(absolute_size - reader.tell())

    return ATR1Data(attributes, size_per_attribute, string_table)


def read_decoded_atr1(reader: FileReader, config: AttributeConfig) -> ATR1Data:
    # String table as a list is not necessary for decoded attributes
    # It is easier to save all changes from the user  when writing
    # to recreate the table from all the string parameters in every attribute
    string_table = None

    section_start = reader.tell()

    attr_count = reader.read_uint32()
    size_per_attribute = reader.read_uint32()

    attributes, attr_start = [], reader.tell()

    for i in range(attr_count):
        reader.seek(attr_start + i * size_per_attribute)

        attribute = {}
        for definition in config.definitions:
            if definition.datatype is LMS_DataType.STRING:
                last = reader.tell() + 4
                reader.seek(section_start + reader.read_uint32())
                value = LMS_Field(reader.read_encoded_string(), definition)
                reader.seek(last)
            else:
                value = read_field(reader, definition)

            attribute[definition.name] = value

        attributes.append(LMS_FieldMap(attribute))

    return ATR1Data(attributes, size_per_attribute, string_table)


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
