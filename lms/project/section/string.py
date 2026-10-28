from lms.fileio.io import FileReader, FileWriter


def read_strings(reader: FileReader, four_byte_count: bool) -> tuple[str]:
    string_list = []

    start = reader.tell() + 4
    count = reader.read_uint32() if four_byte_count else reader.read_uint16()
    reader.seek(start)

    for offset in reader.read_offset_array(count):
        reader.seek(offset)
        string = reader.read_encoded_string()
        string_list.append(string)

    return string_list


def write_strings(
    writer: FileWriter, strings: list[str], four_byte_count: bool
) -> None:
    data_start = writer.tell()

    if four_byte_count:
        writer.write_uint32(len(strings))
    else:
        writer.write_uint16(len(strings))
        writer.write_bytes(b"\x00\x00")

    writer.write_bytes(b"\x00" * len(strings) * 4)

    offset = 4 * len(strings) + 4

    for i, string in enumerate(strings):
        writer.seek(data_start + 4 + (4 * i))
        writer.write_uint32(offset)
        writer.seek(offset + data_start)
        offset += writer.write_encoded_string(string)
