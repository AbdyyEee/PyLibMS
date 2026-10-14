from lms.fileio.io import FileReader
from lms.project.definitions.style import LMS_Style

NO_VALUE = 0xFFFFFFFF

def read_styles(reader: FileReader) -> tuple[LMS_Style, ...]:
    styles = []

    count = reader.read_uint32()
    for _ in range(count):
        region_width = reader.read_uint32()
        line_number = reader.read_uint32()
        font_index = reader.read_uint32()
        color_index = reader.read_uint32()

        if color_index == NO_VALUE:
            color_index = None

        if font_index == NO_VALUE:
            font_index = None

        styles.append(LMS_Style(region_width, line_number, font_index, color_index))

    return styles
