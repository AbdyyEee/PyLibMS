"""
IO interface for ``MSBF`` files.
"""
from typing import BinaryIO, Sequence

from lms.common.lms_exceptions import LMS_Error, LMS_UnsupportedSectionError
from lms.common.stream.fileinfo import read_file_info, write_file_info, write_file_size
from lms.common.stream.hashtable import read_labels, write_labels
from lms.common.stream.section import read_section_data, write_section
from lms.fileio.io import FileReader, FileWriter
from lms.flowchart.flw3 import read_flw3, write_flw3
from lms.flowchart.msbf import MSBF
from lms.message.msbt import MSBT
from lms.titleconfig.definitions.nodes import NodeConfig

__all__ = ("read_msbf", "read_msbf_path", "write_msbf", "write_msbf_path")


def read_msbf_path(
        file_path: str,
        *,
        config: NodeConfig | None = None,
        msbt: MSBT | None = None,
        msbt_files: Sequence[MSBT] | None = None
) -> MSBF:
    """
    Reads a MSBF file from a path.

    :param file_path: path to the MSBF file.
    :param config: the node configuration to use.
    :param msbt_files: sequence of MSBT files utilized for converting ``LMS_MessageNode.msbt_index`` into a real objects.
    :param msbt: Override for decoding message nodes to force all ``LMS_MessageNode`` nodes to utilize this MSBT. Best when
    you know a file utilizes only one MSBT.

    =====
    Usage
    =====
    >>> msbf = read_msbf_path("path/to/file.msbf")
    """
    with open(file_path, "rb") as stream:
        return read_msbf(stream, config=config, msbt=msbt, msbt_files=msbt_files)


def read_msbf(
        stream: BinaryIO | bytes,
        *,
        config: NodeConfig | None = None,
        msbt: MSBT | None = None,
        msbt_files: Sequence[MSBT] | None = None
) -> MSBF:
    """
    Reads a MSBF file from a stream.

    :param stream: stream to read the file from.
    :param config: the node configuration to use.
    :param msbt_directory: the directory of MSBT files, use for LMS_MessageNodes to auto determine the MSBT per node.
    :param msbt: Override for decoding message nodes to force all LMS_MessageNodes to utilize this MSBT. Best when
    you know a file utilizes only one MSBT.
    =====
    Usage
    =====
    >>> msbf = read_msbf(stream)
    """
    reader = FileReader(stream)
    file_info = read_file_info(reader, MSBF.MAGIC)

    if msbt is not None and msbt_files:
        raise ValueError("There may only be one of a directory or MSBT provided.")

    msbf = MSBF(file_info)
    for magic, size in read_section_data(reader, file_info.section_count):
        match magic:
            case "FLW3":
                entry_nodes = read_flw3(reader, config, msbt, msbt_files)
            case "FEN1":
                labels, slot_count = read_labels(reader)
            case "REF1":
                raise LMS_UnsupportedSectionError("""REF1 was found in the MSBF file! Please report this file as an issue
                                                  in the PyLibMS repository https://github.com/AbdyyEee/PylibMS""")

    for i, label in enumerate(labels.values()):
        entry_nodes[i].name = label
        msbf.add_flowchart(label, entry_nodes[i])

    msbf.slot_count = slot_count
    return msbf


def write_msbf_path(file_path: str, file: MSBF) -> None:
    """
    Writes a MSBF file to a given file path. If the target path does not exist, it will be created.

    :param file_path: the path to write the file to.
    :param file: the file object.

    =====
    Usage
    =====
    >>> write_msbf("path/to/file.msbf", msbt)
    """
    with open(file_path, "wb") as stream:
        data = write_msbf(file)
        stream.write(data)


def write_msbf(file: MSBF) -> bytes:
    """
    Writes a MSBF file.

    :param file: The MSBF file.

    =====
    Usage
    =====
    >>> data = write_msbf(msbf)
    """
    if not isinstance(file, MSBF):
        raise LMS_Error(f"File provided is not valid. Expected MSBT got {type(file)}.")

    writer = FileWriter(file.info.encoding)
    write_file_info(writer, MSBF.MAGIC, file.info)

    # Real IDs that must be sequential will be written to the stream
    # Saved here so ids aren't mutated in the current state
    stream_ids = {node: stream_id for stream_id, node in enumerate(file)}
    index_map = {entry.name: stream_ids[entry] for entry in file.entry_nodes}

    write_section(writer, "FLW3", write_flw3, list(file.nodes.values()), stream_ids)
    write_section(
        writer,
        "FEN1",
        write_labels,
        list(file.flowcharts.keys()),
        file.slot_count,
        index_map,
    )
    write_file_size(writer)
    return writer.get_data()
