import os
from pathlib import Path
from typing import TYPE_CHECKING

from lms.source_extension import FileExtension
from lms.message.msbtio import read_msbt_path

if TYPE_CHECKING:
    from lms.flowchart.msbf import MSBF
    from lms.message.msbt import MSBT
    from lms.message.umsbt import UMSBT

from lms.titleconfig.definitions.nodes import NodeConfig
from lms.titleconfig.definitions.project import Project



# Class that maps virtual source paths into real paths
# Files in projects function as paths to a virtual .msbt/.umsbt/.msbf file,
# given a message root these files are resolved automatically to their binary and read
class SourceResolver:
    def __init__(self, project: Project, message_root: str | os.PathLike[str], node_config: NodeConfig):
        self._project = project
        self._message_root = Path(message_root)
        self._node_config = node_config

        self.resolved_cache: dict[str, MSBT | UMSBT | MSBF] = {}
        self._msbt_extension = FileExtension.MSBT

        for _ in self.message_root.rglob(f"*{FileExtension.UMSBT}"):
            self._msbt_extension = FileExtension.UMSBT
            break

    @property
    def project(self) -> Project:
        return self._project

    @property
    def message_root(self) -> Path:
        return self._message_root

    @property
    def node_config(self) -> NodeConfig:
        return self._node_config

    def resolve_msbt(self, source_index: int) -> MSBT | UMSBT:
        return self.resolve_source(source_index, self._msbt_extension)

    def resolve_source(self, source_index: int, extension: FileExtension) -> MSBT | UMSBT | MSBF:
        from lms.message.msbtio import read_msbt_path
        from lms.message.umsbtio import read_umsbt_path
        from lms.flowchart.msbfio import read_msbf_path

        # File is in the cache, retrieve it instantly
        source_path = self.project.sources[source_index]
        filename = os.path.basename(source_path).replace(extension.source_format, extension)

        if filename in self.resolved_cache:
            return self.resolved_cache[filename]

        real_path = None
        for path in self.message_root.rglob(filename):
            real_path = path
            break

        if real_path is None:
            raise ValueError(
                f"The source {source_path} could not be mapped to a file in the message root!"
            )

        match extension:
            case FileExtension.MSBT:
                file = read_msbt_path(real_path, project=self.project)
            case FileExtension.UMSBT:
                file = read_umsbt_path(real_path, project=self.project)
            case FileExtension.MSBF:
                file = read_msbf_path(real_path, node_config=self._node_config, project=self._project,
                                      _source_resolver=self)

        self.resolved_cache[os.path.basename(real_path)] = file
        return file

    def msbt_index_from_file(self, msbt_file: str) -> int:
        try:
            msbt_index = [
                os.path.basename(file) for file in self.project.sources
            ].index(msbt_file.replace(self._msbt_extension, SourceFormat.MSTXT))
        except ValueError as e:
            raise IndexError(
                f"The msbt file '{msbt_file}' does not exist in the source list!"
            ) from e

        return msbt_index

    def msbf_index_from_file(self, msbf_file: str) -> int:
        try:
            msbf_index = [
                os.path.basename(file) for file in self.project.sources
            ].index(msbf_file.replace(FileExtension.MSBF, SourceFormat.MSFLOW))
        except ValueError as e:
            raise IndexError(
                f"The msbf file '{msbf_file}' does not exist in the source list!"
            ) from e

        return msbf_index



