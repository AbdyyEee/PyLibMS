from dataclasses import dataclass


@dataclass
class LMS_Style:
    region_width: int
    line_number: int
    font_index: int | None
    color_index: int | None
    name: str | None = None
