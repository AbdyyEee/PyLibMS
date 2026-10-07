from lms.common import lms_exceptions
from lms.common.lms_constants import (
    SECTION_DATA_START,
    SIZE_OFFSET, LMS_MINIMUM_VERSION,
    LITTLE_ENDIAN_BOM, BIG_ENDIAN_BOM,
)
from lms.common.lms_fileinfo import LMS_FileInfo
from lms.fileio.encoding import FileEncoding
from lms.fileio.endian import FileEndian
from lms.fileio.io import FileReader, FileWriter


def read_file_info(reader: FileReader, expected_magic: str) -> LMS_FileInfo:
    magic = reader.read_string_len(8)

    if magic != expected_magic:
        raise lms_exceptions.LMS_UnexpectedMagicError(
            f"""Invalid magic!' Expected {expected_magic}', got '{magic}'.
            This file may not a valid LMS format or the wrong reading function was utilized."""
        )

    bom = reader.read_bytes(2)

    if bom == LITTLE_ENDIAN_BOM:
        endian = FileEndian.LITTLE
    elif bom == BIG_ENDIAN_BOM:
        endian = FileEndian.BIG
    else:
        raise ValueError(f"Invalid bom found in file '{bom}'!")

    reader.endian = endian
    reader.skip(2)

    encoding = FileEncoding(reader.read_uint8())
    reader.encoding = encoding

    version = reader.read_uint8()

    if version < LMS_MINIMUM_VERSION:
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
        endian,
        encoding,
        version,
        section_count,
    )


def write_file_info(writer: FileWriter, magic: str, file_info: LMS_FileInfo) -> None:
    writer.endian = file_info.endian
    writer.encoding = file_info.encoding

    writer.write_string(magic)
    writer.write_bytes(file_info.endian.byte_order_mark)
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
