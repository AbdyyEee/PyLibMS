from lms.fileio.io import FileReader, FileWriter
from lms.project.definitions.color import LMS_Color


def read_clr1(reader: FileReader) -> tuple[LMS_Color, ...]:
    count = reader.read_uint32()
    return [
        LMS_Color(
            reader.read_uint8(),
            reader.read_uint8(),
            reader.read_uint8(),
            reader.read_uint8(),
        )
        for _ in range(count)
    ]


def write_clr1(writer: FileWriter, colors: list[LMS_Color]) -> None:
    writer.write_uint32(len(colors))
    for color in colors:
        writer.write_uint8(color.red)
        writer.write_uint8(color.green)
        writer.write_uint8(color.blue)
        writer.write_uint8(color.alpha)