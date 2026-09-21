from lms.fileio.encoding import FileEncoding
from lms.fileio.io import FileReader, FileWriter
from lms.message.tag.io.param_io import (
    read_decoded_parameters,
    read_encoded_parameters,
    write_decoded_parameters,
    write_encoded_parameters,
)
from lms.message.tag.lms_tag import LMS_ControlTag, LMS_DecodedTag, LMS_EncodedTag
from lms.message.tag.lms_tagexceptions import LMS_TagReadingError
from lms.titleconfig.definitions.tags import TagConfig, TagDefinition

TAG_PADDING_BYTE = b"\xcd"


def get_tag_indicator(encoding: FileEncoding, is_big_endian: bool):
    start_indicator = int.to_bytes(
        0x0E, encoding.width, "little" if not is_big_endian else "big"
    )
    closing_indicator = int.to_bytes(
        0x0F, encoding.width, "little" if not is_big_endian else "big"
    )
    return start_indicator, closing_indicator


def read_tag(
    reader: FileReader,
    tag_config: TagConfig | None,
    is_closing: bool,
    suppress_tag_errors: bool,
) -> LMS_ControlTag:
    group_id = reader.read_uint16()
    tag_index = reader.read_uint16()
    start = reader.tell()

    if tag_config is None:
        return _read_encoded_tag(reader, group_id, tag_index, is_closing)

    definition = tag_config.get_definition_by_indices(group_id, tag_index)

    # Tags not defined in the config are not considered fallback tags
    # Not all configs will define every tag, so this is simply a measure to still read tags that aren't defined
    if definition is None:
        return _read_encoded_tag(reader, group_id, tag_index, is_closing)

    # There doesn't need to be error handling in this case since there are no parameters for closing tags
    if is_closing:
        return _read_decoded_tag(reader, definition, is_closing=True)

    try:
        tag = _read_decoded_tag(reader, definition)
    except LMS_TagReadingError as e:
        if not suppress_tag_errors:
            raise e

        reader.seek(start)
        return _read_encoded_tag(reader, group_id, tag_index, is_fallback=True)

    return tag


def _read_encoded_tag(
    reader: FileReader,
    group_id: int,
    tag_index: int,
    is_closing: bool = False,
    is_fallback: bool = False,
) -> LMS_EncodedTag:
    if is_closing:
        return LMS_EncodedTag(group_id, tag_index, is_closing=True)

    if not (parameter_size := reader.read_uint16()):
        return LMS_EncodedTag(group_id, tag_index)

    parameters = read_encoded_parameters(reader, parameter_size)
    return LMS_EncodedTag(group_id, tag_index, parameters, is_fallback)


def _read_decoded_tag(
    reader: FileReader, definition: TagDefinition, is_closing: bool = False
) -> LMS_DecodedTag:
    parameter_size = reader.read_uint16()
    end = reader.tell() + parameter_size

    if not parameter_size:
        return LMS_DecodedTag(definition)

    if is_closing:
        return LMS_DecodedTag(definition, is_closing=True)

    parameters = read_decoded_parameters(reader, definition)
    reader.seek(end)
    return LMS_DecodedTag(definition, parameters)


def write_tag(writer: FileWriter, tag: LMS_ControlTag) -> None:
    start_indicator, close_indicator = get_tag_indicator(
        writer.encoding, writer.is_big_endian
    )
    writer.write_bytes(start_indicator if not tag.is_closing else close_indicator)

    writer.write_uint16(tag.group_id)
    writer.write_uint16(tag.tag_index)

    if tag.is_closing:
        return

    if tag.parameters is None:
        writer.write_uint16(0)
        return

    if isinstance(tag, LMS_EncodedTag):
        write_encoded_parameters(writer, tag.parameters)
    else:
        write_decoded_parameters(writer, tag.parameters, tag.group_name, tag.tag_name)
