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

