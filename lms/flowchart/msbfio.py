"""
IO interface for ``MSBF`` files.
"""

import os
from typing import BinaryIO

from lms.common.lms_exceptions import LMS_Error, LMS_UnsupportedSectionError
from lms.common.stream.fileinfo import read_file_info, write_file_info, write_file_size
from lms.common.stream.hashtable import read_labels, write_labels
from lms.common.stream.section import read_section_data, write_section
from lms.fileio.io import FileReader, FileWriter
from lms.flowchart.flw3 import read_flw3, write_flw3
from lms.flowchart.msbf import MSBF, MSBFSection
from lms.source_resolver import SourceResolver
from lms.titleconfig.definitions.nodes import NodeConfig

__all__ = ("read_msbf", "read_msbf_path", "write_msbf", "write_msbf_path")

from lms.titleconfig.definitions.project import Project


def read_msbf_path(file_path: str | os.PathLike[str], *, node_config: NodeConfig | None = None,
                   project: Project | None = None, message_root: os.PathLike[str] | str | None = None,
                   _source_resolver: SourceResolver | None = None) -> MSBF:
    """
    Reads a MSBF file from a path.

    :param file_path: path to the MSBF file.
    :param node_config: the node configuration to use.
    :param project: project object utilized for auto-source resolving.
    :param message_root: root of the message folder/archive. Archives must be extracted first.
    """
    source_resolver = _source_resolver
    if message_root is not None:
        source_resolver = SourceResolver(project, message_root, node_config)

    with open(file_path, "rb") as stream:
        msbf = read_msbf(stream, node_config=node_config, project=project, message_root=message_root,
                         _source_resolver=source_resolver)

        # Add the msbf to cache any circular references
        if source_resolver is not None:
            source_resolver.resolved_cache[os.path.basename(stream.name)] = msbf

    return msbf

def read_msbf(
    stream: BinaryIO | bytes,
    *,
    node_config: NodeConfig | None = None,
    project: Project | None = None,
    message_root: os.PathLike[str] | str | None = None,
    _source_resolver: SourceResolver | None = None
) -> MSBF:
    """
    Reads a MSBF file from a stream.

    :param stream: stream to read the file from.
    :param node_config: the node configuration to use.
    :param project: project object utilized for auto-source resolving.
    :param message_root: root of the message folder/archive. Archives must be extracted for.
    """
    reader = FileReader(stream)

    file_info = read_file_info(reader, MSBF.MAGIC)

    source_resolver = _source_resolver
    if _source_resolver is None:
        source_resolver = SourceResolver(project, message_root, node_config)

    msbf = MSBF(file_info, source_resolver, node_config)
    for magic, size in read_section_data(reader, file_info.section_count):
        match magic:
            case MSBFSection.FLW3:
                entry_nodes = read_flw3(reader, node_config, source_resolver)
            case MSBFSection.FEN1:
                labels, slot_count = read_labels(reader)
            case MSBFSection.REF1:
                raise LMS_UnsupportedSectionError(
                    """REF1 was found in the MSBF file! Please report this file as an issue
                                                  in the PyLibMS repository https://github.com/AbdyyEee/PylibMS"""
                )

    for i, label in enumerate(labels.values()):
        entry_nodes[i].name = label
        msbf.add_flowchart(label, entry_nodes[i])

    msbf.slot_count = slot_count

    return msbf


def write_msbf_path(file_path: str | os.PathLike[str], file: MSBF) -> None:
    """
    Writes a MSBF file to a given file path. If the target path does not exist, it will be created.

    :param file_path: the path to write the file to.
    :param file: the file object.

    """
    with open(file_path, "wb") as stream:
        data = write_msbf(file)
        stream.write(data)


def write_msbf(file: MSBF) -> bytes:
    """
    Writes a MSBF file.

    :param file: The MSBF file.
    """
    if not isinstance(file, MSBF):
        raise LMS_Error(f"File provided is not valid. Expected MSBT got {type(file)}.")

    writer = FileWriter(file.info.encoding)
    write_file_info(writer, MSBF.MAGIC, file.info)

    # Real IDs that must be sequential will be written to the stream
    # Saved here so ids aren't mutated in the current state
    stream_ids = {node: stream_id for stream_id, node in enumerate(file)}
    index_map = {entry.name: stream_ids[entry] for entry in file.entry_nodes}

    write_section(
        writer, MSBFSection.FLW3, write_flw3, list(file.nodes.values()), stream_ids
    )
    write_section(
        writer,
        MSBFSection.FEN1,
        write_labels,
        list(file.flowcharts.keys()),
        file.slot_count,
        index_map,
    )
    write_file_size(writer)
    return writer.get_data()
