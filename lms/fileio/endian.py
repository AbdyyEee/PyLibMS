from enum import Enum
from typing import Literal


class FileEndian(Enum):
    """An enum that represents a file endianness."""

    LITTLE = 0
    BIG = 1

    @property
    def string_name(self) -> Literal["little", "big"]:
        """Name of the endian as a string."""
        return self._name_.lower()

    @property
    def byte_order_mark(self) -> Literal[b"\xFF\xFE", b"\xFE\xFF"]:
        """The BOM of the endian."""
        return b"\xFF\xFE" if self is FileEndian.LITTLE else b"\xFE\xFF"
