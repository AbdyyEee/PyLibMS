import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from lms.message.umsbtio import read_umsbt_path

if TYPE_CHECKING:
    from lms.flowchart.msbf import MSBF
    from lms.message.msbt import MSBT

from lms.titleconfig.definitions.nodes import NodeConfig
from lms.titleconfig.definitions.project import Project, MessageSource


# Class that maps virtual source paths into real paths
# Files in projects function as paths to a virtual .mstxt/.msflow file,
# given a message root these files are resolved automatically to their binary and read
@dataclass
class SourceResolver:
    message_root: Path
    project: Project
    node_config: NodeConfig | None
    uses_umsbt: bool = False
    _resolved_cache: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Determine umsbt/msbt extension
        for _ in self.message_root.rglob("*.umsbt"):
            self.uses_umsbt = True
            break

    def msbt_index_from_file(self, msbt_file: str) -> int:
        try:
            msbt_index = [
                os.path.basename(file) for file in self.project.sources
            ].index(msbt_file.replace(self.msbt_extension, ".mstxt"))
        except ValueError as e:
            raise IndexError(
                f"The msbt file '{msbt_file}' does not exist in the source list!"
            ) from e

        return msbt_index

    def msbf_index_from_file(self, msbf_file: str) -> int:
        try:
            msbf_index = [
                os.path.basename(file) for file in self.project.sources
            ].index(msbf_file.replace(".msbf", ".msflow"))
        except ValueError as e:
            raise IndexError(
                f"The msbf file '{msbf_file}' does not exist in the source list!"
            ) from e

        return msbf_index

    def resolve_msbt_index(self, msbt_index: int) -> MSBT:
        from lms.message.msbtio import read_msbt_path
        from lms.message.umsbtio import read_umsbt_path

        if self.uses_umsbt:
            extension = ".umsbt"
            msbt_io_function = read_umsbt_path
        else:
            extension = ".msbt"
            msbt_io_function = read_msbt_path

        real_path, source_path = self._resolve_source(msbt_index, ".mstxt", extension)

        if real_path is None:
            raise ValueError(
                f"The source {source_path} could not be mapped to a file in the message root!"
            )

        if real_path in self._resolved_cache:
            return self._resolved_cache[real_path]

        msbt = msbt_io_function(real_path, project=self.project)
        self._resolved_cache[real_path] = msbt
        return msbt

    def resolve_msbf_index(self, msbt_index: int) -> MSBF:
        from lms.flowchart.msbfio import read_msbf_path

        real_path, source_path = self._resolve_source(msbt_index, ".msflow", ".msbf")

        if real_path is None:
            raise ValueError(
                f"The source {source_path} could not be mapped to a file in the message root!"
            )

        if real_path in self._resolved_cache:
            return self._resolved_cache[real_path]

        msbf = read_msbf_path(
            real_path,
            node_config=self.node_config,
            project=self.project,
            message_root=self.message_root,
        )
        self._resolved_cache[real_path] = msbf
        return msbf

    def _resolve_source(
        self, source_index: int, source_extension: str, binary_extension: str
    ) -> tuple[Path | None, str]:
        # Technically, CTI1 can store any file to reference by the game and does not have to be ending in
        # mstxt or msflow, however we can ignore that for now since we are only supporting resolving external msbt/msbfs
        source_path = self.project.sources[source_index]

        # Resolve the file itself, the source directory may not exist since those were generated
        # in Nintendo's environment and the official libMessageStudio tool.
        # E.g, Tomodachi Life 3DS refers to a directory called `Confession/ConfessionBeach.mstxt` in the MSBP, yet
        # 'Confession' is not a folder in the RomFS. However, `Drama_Confession/ArcBase/ConfessionBeach.msbt`
        # is a valid directory. The above also applies to external jump references in other MSBF files.
        filename = os.path.basename(source_path).replace(
            source_extension, binary_extension
        )

        for path in self.message_root.rglob(filename):
            return path, source_path

        return None, source_path
