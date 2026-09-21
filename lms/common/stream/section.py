from typing import Any, Callable, Generator

from lms.fileio.io import FileReader, FileWriter

SECTION_PADDING_BYTE = b"\xab"
SECTION_ALIGNMENT = 16


def read_section_data(
    reader: FileReader, section_count: int
) -> Generator[tuple[str, int], Any, None]:
    reader.seek(0x20)
    for _ in range(section_count):
        magic = reader.read_string_len(4)
        size = reader.read_uint32()

        reader.skip(8)
        end = reader.tell() + size

        yield magic, size

        reader.seek(end)
        reader.align(16)


def write_section(
    writer: FileWriter,
    magic: str,
    section_call: Callable,
    data: list[Any],
    *write_arguments: Any,
) -> None:
    writer.write_string(magic)
    size_offset = writer.tell()

    writer.write_uint32(0)
    writer.write_bytes(b"\x00" * 8)
    data_start = writer.tell()

    section_call(writer, data, *write_arguments)

    _write_end_data(writer, data_start, size_offset)


def write_unsupported_section(writer: FileWriter, magic: str, data: bytes) -> None:
    writer.write_string(magic)
    size_offset = writer.tell()
    writer.write_uint32(0)
    writer.write_bytes(b"\x00" * 8)
    data_start = writer.tell()
    writer.write_bytes(data)
    _write_end_data(writer, data_start, size_offset)


def _write_end_data(writer: FileWriter, data_start: int, size_offset: int) -> None:
    end = writer.tell()
    size = end - data_start
    writer.seek(size_offset)
    writer.write_uint32(size)
    writer.seek(end)
    writer.write_alignment(SECTION_PADDING_BYTE, SECTION_ALIGNMENT)
