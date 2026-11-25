from lms.fileio.io import FileReader, FileWriter


# MKWorld specific section:
# UInt32 font count followed by font names
def read_fnt1(reader: FileReader) -> list[str]:
    count = reader.read_uint32()
    return [reader.read_len_encoded_string(u8_prefix=True) for _ in range(count)]

def write_fnt1(writer: FileWriter, font_names: tuple[str, ...]) -> None:
    writer.write_uint32(len(font_names))
    for name in font_names:
        writer.write_len_encoded_string(name, u8_prefix=True)