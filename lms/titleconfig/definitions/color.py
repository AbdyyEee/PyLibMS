from dataclasses import dataclass
from typing import Self


@dataclass
class Color:
    name: str
    description: str
    red: int
    green: int
    blue: int
    alpha: int

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            data["name"],
            data.get("description", ""),
            data["red"],
            data["green"],
            data["blue"],
            data["alpha"]\
        )