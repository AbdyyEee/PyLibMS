from dataclasses import dataclass
from typing import Self


@dataclass
class Style:
    name: str
    description: str
    region_width: int
    line_number: int
    font_index: int | None
    color_index: int | None

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            data["name"],
            data.get("description", ""),
            data["region_width"],
            data["line_number"],
            data["font_index"],
            data["color"],
            )
