from enum import IntEnum
from typing import Literal


class FileEncoding(IntEnum):
    """An enum that represents a file encoding."""

    UTF8 = 0x00
    UTF16 = 0x01
    UTF32 = 0x02

    def to_string_format(
        self, is_big_endian: bool = False
    ) -> Literal["UTF-8", "UTF-16-BE", "UTF-16-LE", "UTF-32-BE", "UTF-32-LE"]:
        """Converts the FileEncoding to string format."""
        match self:
            case FileEncoding.UTF8:
                return "UTF-8"
            case FileEncoding.UTF16:
                if is_big_endian:
                    return "UTF-16-BE"
                return "UTF-16-LE"
            case FileEncoding.UTF32:
                if is_big_endian:
                    return "UTF-32-BE"
                return "UTF-32-LE"

    @property
    def width(self) -> Literal[1, 2, 4]:
        """The width of the encoding in the stream."""
        match self:
            case FileEncoding.UTF8:
                return 1
            case FileEncoding.UTF16:
                return 2
            case FileEncoding.UTF32:
                return 4

    @property
    def terminator(self) -> bytes:
        """The typical terminator for a string in the encoding."""
        return b"\x00" * self.width
