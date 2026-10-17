from lms.fileio.io import FileReader, FileWriter
from lms.project.definitions.style import LMS_Style

DEFAULT = 0xFFFFFFFF

def read_syl3(reader: FileReader) -> tuple[LMS_Style, ...]:
    styles = []

    count = reader.read_uint32()
    for _ in range(count):
        region_width = reader.read_uint32()
        line_number = reader.read_uint32()
        font_index = reader.read_uint32()
        color_index = reader.read_uint32()

        if color_index == DEFAULT:
            color_index = None

        if font_index == DEFAULT:
            font_index = None

        styles.append(LMS_Style(region_width, line_number, font_index, color_index))

    return styles

def write_syl3(writer: FileWriter, styles: tuple[LMS_Style, ...]) -> None:
    writer.write_uint32(len(styles))

    for style in styles:
        writer.write_uint32(style.region_width)
        writer.write_uint32(style.line_number)
        writer.write_uint32(DEFAULT if style.font_index is None else style.font_index)
        writer.write_uint32(DEFAULT if style.color_index is None else style.color_index)