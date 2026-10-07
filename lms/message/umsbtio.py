"""
IO interface for ``MSBT`` files.
"""
import os
from typing import Mapping, BinaryIO

from lms.common import lms_exceptions
from lms.fileio.io import FileReader, FileWriter
from lms.message.msbt import MSBT
from lms.message.msbtio import read_msbt, write_msbt
from lms.message.umsbt import UMSBT
from lms.titleconfig.definitions.attribute import AttributeConfig
from lms.titleconfig.definitions.tags import TagConfig

__all__ = ("read_umsbt_path", "read_umsbt_directory", "read_umsbt", "write_umsbt_path", "write_umsbt")

UMSBT_EXTENSION = ".umsbt"
UMSBT_ALIGNMENT = 16
SIZE_PER_METADATA = 8


def read_umsbt_path(
        file_path: str | os.PathLike[str], *,
        attribute_config: AttributeConfig | None = None,
        tag_config: TagConfig | None = None,
        suppress_tag_errors: bool = False,
) -> UMSBT:
    """
    Reads and retrieves a UMSBT file from a given path.

    :param file_path: the path to the UMSBT file.
    :param attribute_config: the attribute config to use for decoding attributes.
    :param tag_config: the tag config to use for decoding tags.
    :param suppress_tag_errors: when a tag config is used, suppress any errors while reading decoded tags.

    =====
    Usage
    =====
    >>> umsbt = read_umsbt_path("path/to/file.umsbt")
    """
    with open(file_path, "rb") as stream:
        umsbt = read_umsbt(stream,
                           attribute_config=attribute_config,
                           tag_config=tag_config,
                           suppress_tag_errors=suppress_tag_errors)

    return umsbt


def read_umsbt_directory(directory: str | os.PathLike[str], *,
                         attribute_config: AttributeConfig | None = None,
                         tag_config: TagConfig | None = None,
                         suppress_tag_errors: bool = False,
                         ignore_extensions: bool = False) -> Mapping[str, tuple[MSBT, ...]]:
    """
    Reads and retrieves all UMSBT files from a given directory.

    :param directory: directory of UMSBT files. All files must have the `.umsbt` extension (unless ``ignore_extensions``
    is True)
    :param attribute_config: the attribute config to use for decoding attributes.
    :param tag_config: the tag config to use for decoding tags.
    :param suppress_tag_errors: when a tag config is used, suppress any errors while reading decoded tags.
    :param ignore_extensions: ignore the extensions in the directory.

    =====
    Usage
    =====
    >>> umsbts = read_msbt_directory("path/to/directory")
    """
    files: dict[str, tuple[MSBT, ...]] = {}

    for file in os.listdir(directory):
        if not file.endswith(UMSBT_EXTENSION) and not ignore_extensions:
            raise ValueError("This directory contains a non-UMSBT file. "
                             "Only directories with UMSBT files can be used! Set ignore_extensions to True to ignore"
                             "this error.")

        umsbt = read_umsbt_path(os.path.join(directory, file),
                                attribute_config=attribute_config,
                                tag_config=tag_config, suppress_tag_errors=suppress_tag_errors)
        files[os.path.basename(file)] = umsbt

    return files

def read_umsbt(
        stream: BinaryIO | bytes, *,
        attribute_config: AttributeConfig | None = None,
        tag_config: TagConfig | None = None,
        suppress_tag_errors: bool = False,
) -> UMSBT:
    """
    Reads and retrieves a UMSBT file from a specified stream.

    :param stream: an ``IOBase``, ``BytesIO``, ``memoryview``, or ``bytes`` object.
    :param attribute_config: the attribute config to use for decoding attributes.
    :param tag_config: the tag config to use for decoding tags.
    :param suppress_tag_errors: when a tag config is used, suppress any errors while reading decoded tags.

    =====
    Usage
    =====
    >>> umsbt = read_umsbt(stream)
    """
    reader = FileReader(stream)
    data_start = reader.read_uint32()

    offsets, sizes = [], []

    reader.seek(0)
    while reader.tell() < data_start:
        offset, size = reader.read_uint32(), reader.read_uint32()

        # Reached padding section
        if offset == 0 and size == 0:
            break

        offsets.append(offset)
        sizes.append(size)

    files = []
    for i, (offset, size) in enumerate(zip(offsets, sizes)):
        reader.seek(offset)
        files.append(read_msbt(reader.read_bytes(size),
                               attribute_config=attribute_config,
                               tag_config=tag_config,
                               suppress_tag_errors=suppress_tag_errors))

    return UMSBT(files)


def write_umsbt_path(file_path: str | os.PathLike[str], file: UMSBT) -> None:
    """
    Writes a UMSBT file to a given file path. If the target path does not exist, it will be created.

    :param file_path: the path to write the file to.
    :param file: the UMSBT file object.

    =====
    Usage
    =====
    >>> write_umsbt_path("path/to/file.umsbt", umsbt)
    """
    with open(file_path, "wb") as stream:
        data = write_umsbt(file)
        stream.write(data)


def write_umsbt(file: UMSBT) -> bytes:
    """
    Writes a UMSBT file and returns the data.

    :param file: a UMSBT object.

    =====
    Usage
    =====
    >>> data = write_umsbt(umsbt)
    """
    if not isinstance(file, UMSBT):
        raise lms_exceptions.LMS_Error(
            f"File provided is not valid. Expected UMSBT got {type(file)}."
        )

    writer = FileWriter()
    msbt_count = len(file)
    writer.write_bytes(b"\x00" * (msbt_count * SIZE_PER_METADATA))

    writer.write_alignment(b"\x00", UMSBT_ALIGNMENT)
    writer.write_bytes(b"\x00" * UMSBT_ALIGNMENT)

    for i, msbt in enumerate(file):
        offset = writer.tell()
        data = write_msbt(msbt)
        writer.write_bytes(data)
        last_position = writer.tell()

        writer.seek(i * SIZE_PER_METADATA)
        writer.write_uint32(offset)
        writer.write_uint32(len(data))
        writer.seek(last_position)

    return writer.get_data()
