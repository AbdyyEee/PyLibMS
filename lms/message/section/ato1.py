from lms.fileio.io import FileReader, FileWriter

NO_ATTR = 0xFFFFFFFF


def read_ato1(reader: FileReader, section_size: int) -> list[int]:
    # No count of offsets is stored, so use section_size / 4 (u32 per offset)
    return [
        None if (offset := reader.read_uint32()) == NO_ATTR else offset
        for _ in range(section_size // 4)
    ]


def write_ato1(writer: FileWriter, offsets: list[int | None]) -> None:
    for offset in offsets:
        writer.write_uint32(NO_ATTR if offset is None else offset)
