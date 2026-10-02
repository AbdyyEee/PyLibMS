from lms.fileio.io import FileReader


def read_strings(reader: FileReader, four_byte_count: bool) -> tuple[str]:
    string_list = []

    start = reader.tell() + 4
    count = reader.read_uint32() if four_byte_count else reader.read_uint16()
    reader.seek(start)

    for offset in reader.read_offset_array(count):
        reader.seek(offset)
        string = reader.read_encoded_string()
        string_list.append(string)

    return tuple(string_list)
