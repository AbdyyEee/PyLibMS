from lms.common import lms_exceptions
from lms.common.lms_constants import (
    BIG_ENDIAN_BOM,
    SECTION_DATA_START,
    LITTLE_ENDIAN_BOM,
    SIZE_OFFSET,
)
from lms.common.lms_fileinfo import LMS_FileInfo
from lms.fileio.encoding import FileEncoding
from lms.fileio.io import FileReader, FileWriter


def read_file_info(reader: FileReader, expected_magic: str) -> LMS_FileInfo:
    magic = reader.read_string_len(8)

    if magic != expected_magic:
        raise lms_exceptions.LMS_UnexpectedMagicError(
            f"""Invalid magic!' Expected {expected_magic}', got '{magic}'.
            This file may not a valid LMS format or the wrong reading function was utilized."""
        )

    is_big_endian = reader.read_bytes(2) == BIG_ENDIAN_BOM
    reader.is_big_endian = is_big_endian

    reader.skip(2)

    encoding = FileEncoding(reader.read_uint8())
    reader.encoding = encoding

    version = reader.read_uint8()

    if version < 3:
        raise lms_exceptions.LMS_UnsupportedFileVersionError(
            "Only version 3+ files are supported!"
        )

    section_count = reader.read_uint16()

    reader.skip(2)
    file_size = reader.read_uint32()

    reader.seek(0, 2)
    if file_size != (real_size := reader.tell()):
        raise lms_exceptions.LMS_MisalignedSizeError(
            f"File size is misaligned!` Got {file_size} expected {real_size}."
        )

    reader.seek(SECTION_DATA_START)

    return LMS_FileInfo(
        is_big_endian,
        encoding,
        version,
        section_count,
    )


def write_file_info(writer: FileWriter, magic: str, file_info: LMS_FileInfo) -> None:
    writer.is_big_endian = file_info.is_big_endian
    writer.encoding = file_info.encoding

    writer.write_string(magic)
    writer.write_bytes(
        LITTLE_ENDIAN_BOM if not file_info.is_big_endian else BIG_ENDIAN_BOM
    )
    writer.write_bytes(b"\x00\x00")

    writer.write_uint8(file_info.encoding.value)
    writer.write_uint8(file_info.version)
    writer.write_uint16(file_info.section_count)

    writer.write_bytes(b"\x00\x00")
    writer.write_bytes(b"\x00" * 4)
    writer.write_bytes(b"\x00" * 10)
    writer.seek(SECTION_DATA_START)


def write_file_size(writer: FileWriter):
    writer.seek(SIZE_OFFSET)
    writer.write_uint32(writer.get_stream_size())
