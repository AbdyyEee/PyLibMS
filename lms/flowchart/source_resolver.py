import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lms.flowchart.msbf import MSBF
    from lms.message.msbt import MSBT

from lms.titleconfig.definitions.nodes import NodeConfig
from lms.titleconfig.definitions.project import Project, MessageSource


@dataclass(frozen=True)
class SourceResolver:
    message_root: os.PathLike[str] | str
    project: Project | None
    node_config: NodeConfig | None
    _resolved_cache: dict[str, MSBT | MSBF] = field(default_factory=dict)

    def resolve_msbt_index(self, msbt_index: int) -> MSBT:
        from lms.message.msbtio import read_msbt_path

        real_path, source_path = self._resolve_source(msbt_index, ".mstxt", ".msbt")

        if real_path is None:
            return None

        if real_path in self._resolved_cache:
            return self._resolved_cache[real_path]

        msbt = read_msbt_path(real_path, project=self.project)
        self._resolved_cache[real_path] = msbt
        return msbt

    def resolve_msbf_index(self, msbt_index: int) -> MSBT:
        from lms.flowchart.msbfio import read_msbf_path

        real_path, source_path = self._resolve_source(msbt_index, ".msflow", ".msbf")

        if real_path is None:
            return None, source_path

        if real_path in self._resolved_cache:
            return self._resolved_cache[real_path]

        msbf = read_msbf_path(real_path, config=self.node_config, project=self.project, message_root=self.message_root)
        self._resolved_cache[real_path] = msbf
        return msbf

    def _resolve_source(self, source_index: int, source_extension: str, binary_extension: str) -> tuple[Path | None, str]:
        # Technically, CTI1 can store any file to reference by the game and does not have to be ending in
        # mstxt or msflow, however we can ignore that for now since we are only supporting resolving external msbt/msbfs
        source_path = self.project.sources[source_index]

        # Resolve the file itself, the source directory may not exist since those were generated
        # in Nintendo's environment and the official libMessageStudio tool.
        # E.g, Tomodachi Life 3DS refers to a directory called `Confession/ConfessionBeach.mstxt` in the MSBP, yet
        # 'Confession' is not a folder in the RomFS. However, `Drama_Confession/ArcBase/ConfessionBeach.msbt`
        # is a valid directory. The above also applies to external jump references in other MSBF files.
        filename = os.path.basename(source_path).replace(source_extension, binary_extension)

        for path in Path(self.message_root).rglob(filename):
            if path.name == filename:
                return path, source_path

        return None, source_path
