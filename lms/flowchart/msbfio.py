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
from lms.titleconfig.config import TitleConfig
from lms.titleconfig.definitions.nodes import NodeConfig

__all__ = ("read_msbf", "read_msbf_path", "write_msbf", "write_msbf_path")

from lms.titleconfig.definitions.project import Project


def read_msbf_path(file_path: str | os.PathLike[str], *,
                   config: TitleConfig | None = None,
                   node_config: NodeConfig | None = None,
                   project: Project | None = None, message_root: os.PathLike[str] | str | None = None,
                   language: str | None = None,
                   _source_resolver: SourceResolver | None = None) -> MSBF:
    """
    Reads a MSBF file from a path.

    :param file_path: path to the MSBF file.
    :param node_config: the node configuration to use.
    :param project: project object utilized for auto-source resolving.
    :param message_root: root of the message folder/archive. Archives must be extracted first.
    :param language: language name from a configuration to map UMSBT to msbt files in message nodes.
    """
    with open(file_path, "rb") as stream:
        msbf = read_msbf(stream, config=config, node_config=node_config, project=project, message_root=message_root,
                         language=language, _source_resolver=_source_resolver)

    return msbf



def read_msbf(
    stream: BinaryIO | bytes,
    *,
    config: TitleConfig | None = None,
    node_config: NodeConfig | None = None,
    project: Project | None = None,
    message_root: os.PathLike[str] | str | None = None,
    language: str | None = None,
    stream_name: str | None = None,
    _source_resolver: SourceResolver | None = None
) -> MSBF:
    """
    Reads a MSBF file from a stream.

    To resolve MSBF sources, ideally ``stream`` should implement an `@name` attribute in the case there are circular
    references. Otherwise, ``stream_name`` can be provided instead.

    :param stream: stream to read the file from.
    :param config: a TitleConfig. Automatically utilizes the global node config and project and UMSBT language map.
    :param node_config: override for a node configuration to use.
    :param project: project object utilized for auto-source resolving.
    :param message_root: root of the message folder/archive. Archives must be extracted for.
    :param language: language name from a configuration to map UMSBT to msbt files in message nodes, i.e. ``USen``.
    :param stream_name: optional stream name argument to link circular MSBF jump node references.
    """
    reader = FileReader(stream)

    file_info = read_file_info(reader, MSBF.MAGIC)

    if config is not None:
        if node_config is None:
            node_config = config.global_node_config
        if project is None:
            project = config.global_project

    if config is None and language is not None:
        raise ValueError("A config must be provided for UMSBT language mapping!")

    source_resolver = _source_resolver

    if _source_resolver is None and message_root is not None:
        source_resolver = SourceResolver(
            config,
            project,
            message_root,
            node_config,
            language)

    msbf = MSBF(file_info, source_resolver, node_config)

    for magic, size in read_section_data(reader, file_info.section_count):
        match magic:
            case MSBFSection.FLW3:
                entry_nodes, external_jumps = read_flw3(reader, node_config, source_resolver)
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

    # If the stream has a name property this will work as intended
    # however, since raw byte streams can be passed we can account this with stream_name argument
    if stream_name is None:
        stream_name = getattr(stream, "name", None)

    if _source_resolver is not None and stream_name is None:
        raise ValueError("To resolve sources provide a filename or stream should implement a name attribute!")

    filename_key = os.path.basename(stream_name) if isinstance(stream_name, (str, os.PathLike[str])) else None

    if source_resolver is not None:

        if stream_name is not None:
            source_resolver.resolved_cache[filename_key] = msbf

        try:
            # Resolve the external jumps safely now
            for jump, next_node_id in external_jumps:
                if next_node_id is None:
                    continue
                jump.set_next_node(jump.msbf[next_node_id])
        except Exception:
            source_resolver.resolved_cache.clear()
            raise

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
