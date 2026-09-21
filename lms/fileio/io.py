from __future__ import annotations

import struct
from typing import BinaryIO, Generator

from io import BytesIO, IOBase
from lms.fileio.encoding import FileEncoding

PADDING_BYTE = b"\x00"

STRUCT_TYPES = {
    "little": {
        "uint8": "<B",
        "uint16": "<H",
        "uint32": "<I",
        "int8": "<b",
        "int16": "<h",
        "int32": "<i",
        "float": "<f",
    },
    "big": {
        "uint8": ">B",
        "uint16": ">H",
        "uint32": ">I",
        "int8": ">b",
        "int16": ">h",
        "int32": ">i",
        "float": ">f",
    },
}


class FileReader:
    def __init__(self, data: BinaryIO | bytes, big_endian: bool = False):
        if isinstance(data, IOBase):
            self._stream = data
        elif isinstance(data, (bytes, bytearray, memoryview)):
            self._stream = BytesIO(data)
        else:
            raise TypeError("The stream provided is not valid!")

        self.encoding = FileEncoding.UTF8
        self.is_big_endian = big_endian

    def tell(self) -> int:
        return self._stream.tell()

    def skip(self, length: int) -> None:
        self._stream.read(length)

    def align(self, alignment: int) -> None:
        alignment = (-self.tell() % alignment + alignment) % alignment
        self.skip(alignment)

    def read_bytes(self, length: int) -> bytes:
        return self._stream.read(length)

    def seek(self, offset: int, whence: int = 0) -> None:
        if offset < 0:
            self._stream.seek(self.tell() + offset)
        else:
            self._stream.seek(offset, whence)

    def read_offset_array(self, count: int) -> Generator[int, None, None]:
        start = self.tell() - 4
        for _ in range(count):
            last = self.tell() + 4
            yield self.read_uint32() + start
            self.seek(last)

    def read_uint16_array(self, count: int) -> list[int]:
        return [self.read_uint16() for _ in range(count)]

    def read_int8(self) -> int:
        return struct.unpack(self._get_datatype("int8"), self._stream.read(1))[0]

    def read_int16(self) -> int:
        return struct.unpack(self._get_datatype("int16"), self._stream.read(2))[0]

    def read_int32(self) -> int:
        return struct.unpack(self._get_datatype("int32"), self._stream.read(4))[0]

    def read_uint8(self) -> int:
        return struct.unpack(self._get_datatype("uint8"), self._stream.read(1))[0]

    def read_uint16(self) -> int:
        return struct.unpack(self._get_datatype("uint16"), self._stream.read(2))[0]

    def read_uint32(self) -> int:
        return struct.unpack(self._get_datatype("uint32"), self._stream.read(4))[0]

    def read_float32(self) -> float:
        return struct.unpack(self._get_datatype("float"), self._stream.read(4))[0]

    def read_string_offset(self, section_start: int) -> str:
        offset = self.read_uint32()
        last_position = self.tell()
        self.seek(section_start + offset)
        string = self.read_encoded_string()
        self.seek(last_position)
        return string

    def read_string_len(self, length: int) -> str:
        return self._stream.read(length).decode("UTF-8")

    def read_encoded_string(self):
        message = b""
        while (
            raw_char := self.read_bytes(self.encoding.width)
        ) != self.encoding.terminator:
            message += raw_char
        return message.decode(self.encoding.to_string_format(self.is_big_endian))

    def read_len_string_encoded(self):
        self.align(self.encoding.width)
        length = self.read_uint16()
        return self.read_bytes(length).decode(
            self.encoding.to_string_format(self.is_big_endian)
        )

    def _get_datatype(self, name: str) -> str:
        return STRUCT_TYPES["little" if not self.is_big_endian else "big"][name]


class FileWriter:
    def __init__(self, encoding: FileEncoding):
        self.data = BytesIO(b"")
        self.encoding = encoding
        self.is_big_endian = False

    def skip(self, length: int) -> None:
        self.data.seek(length, 1)

    def get_stream_size(self) -> int:
        last_position = self.tell()
        self.seek(0, 2)
        size = self.tell()
        self.seek(last_position)
        return size

    def write_bytes(self, data: bytes) -> None:
        self.data.write(data)

    def seek(self, offset: int, whence: int = 0) -> None:
        self.data.seek(offset, whence)

    def tell(self) -> int:
        return self.data.tell()

    def write_alignment(self, data: bytes, alignment: int) -> None:
        self.write_bytes(data * self._align(self.tell(), alignment))

    def write_uint16_array(self, array: list[int]) -> None:
        for number in array:
            self.write_uint16(number)

    def write_int8(self, value: int) -> None:
        self.data.write(struct.pack(self._get_datatype("int8"), value))

    def write_int16(self, value: int) -> None:
        self.data.write(struct.pack(self._get_datatype("int16"), value))

    def write_int32(self, value: int) -> None:
        self.data.write(struct.pack(self._get_datatype("int32"), value))

    def write_uint8(self, value: int) -> None:
        self.data.write(struct.pack(self._get_datatype("uint8"), value))

    def write_uint16(self, value: int) -> None:
        self.data.write(struct.pack(self._get_datatype("uint16"), value))

    def write_uint32(self, value: int) -> None:
        self.data.write(struct.pack(self._get_datatype("uint32"), value))

    def write_float32(self, value: float) -> None:
        self.data.write(struct.pack(self._get_datatype("float"), value))

    def write_string(self, string: str):
        self.write_bytes(string.encode("UTF-8"))

    def write_len_encoded_string(self, string: str) -> None:
        self.write_uint16(len(string) * self.encoding.width)
        self.write_encoded_string(string, False)

    def write_encoded_string(self, string: str, terminate: bool = True):
        self.write_bytes(
            string.encode(self.encoding.to_string_format(self.is_big_endian))
        )
        if terminate:
            self.write_bytes(b"\x00" * self.encoding.width)

    def _align(self, number: int, alignment: int) -> int:
        return (-number % alignment + alignment) % alignment

    def _get_datatype(self, name: str) -> str:
        return STRUCT_TYPES["little" if not self.is_big_endian else "big"][name]

    def get_data(self) -> bytes:
        return self.data.getvalue()
