import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import case

from lms.source_extension import FileExtension
from lms.titleconfig.config import TitleConfig

if TYPE_CHECKING:
    from lms.flowchart.msbf import MSBF
    from lms.message.msbt import MSBT
    from lms.message.umsbt import UMSBT

from lms.titleconfig.definitions.nodes import NodeConfig
from lms.titleconfig.definitions.project import Project

# Class that maps virtual source paths into real paths.
# Files in projects function as paths to a virtual .msbt/.msbf file,
# given a message root these files are resolved automatically to their binary and read
class SourceResolver:
    def __init__(self,
                 config: TitleConfig,
                 project: Project,
                 message_root: str | os.PathLike[str],
                 node_config: NodeConfig,
                 language: str | None = None):
        self._config = config
        self._project = project
        self._message_root = Path(message_root or "")
        self._node_config = node_config

        self.resolved_cache: dict[str, MSBT | UMSBT | MSBF] = {}
        self._msbt_extension = FileExtension.MSBT

        self._file_map: dict[str, list[Path]] = {}
        for path in self._message_root.rglob("*"):
            if not path.is_file():
                continue

            extension = path.suffix
            if extension not in [FileExtension.MSBT, FileExtension.MSBF, FileExtension.UMSBT]:
                continue

            self._file_map.setdefault(path.name, []).append(path)


        self._language = language

    def validate(self) -> None:
        if not self._message_root:
            raise ValueError("No message root was provided!")

        if not self._project:
            raise ValueError("No project was provided!")

    def retrieve_filename(self, source_index: int) -> str:
        try:
            source_path = self._project.sources[source_index]
        except IndexError as e:
            raise IndexError(f"The source '{source_index}' could not be mapped to a file in the message root!") from e

        extension = {
            FileExtension.MSBT.source_format: self._msbt_extension,
            FileExtension.MSBF.source_format: FileExtension.MSBF,
        }[Path(source_path).suffix]
        stem = Path(source_path).stem

        # Add language suffix
        if extension is FileExtension.UMSBT:
            if self._language is None:
                raise ValueError("No language was provided to map a UMSBT to a MSBT!")

            return f"{stem}_{self._language}{FileExtension.MSBT}"

        return f"{stem}{extension}"

    def resolve_msbt(self, source_index: int) -> MSBT | UMSBT:
        return self.resolve_source(source_index, self._msbt_extension)

    # TODO: narrow matches better by not stripping base paths when utilizing os.path.basename
    def resolve_source(self, source_index: int, extension: FileExtension) -> MSBT | MSBF:
        from lms.message.msbtio import read_msbt_path
        from lms.message.umsbtio import read_umsbt_path
        from lms.flowchart.msbfio import read_msbf_path

        # File is in the cache, retrieve it instantly
        try:
            source_path = self._project.sources[source_index]
        except KeyError as e:
            raise KeyError(f"The source '{source_path}' could not be mapped to a file in the message root!") from e

        filename = os.path.basename(source_path).replace(extension.source_format, extension)

        if filename in self.resolved_cache:
            return self.resolved_cache[filename]

        try:
            source_path = self._project.sources[source_index]
        except KeyError as e:
            raise KeyError(f"The source '{source_path}' could not be mapped to a file in the message root!") from e

        filename = os.path.basename(source_path).replace(extension.source_format, extension)

        if filename in self.resolved_cache:
            return self.resolved_cache[filename]

        if (matches := self._file_map.get(filename)) is None:
            raise KeyError(f"The source '{source_path}' could not be mapped to a file in the message root!")

        real_path = matches[0]
        match extension:
            case FileExtension.MSBT:
                file = read_msbt_path(real_path, project=self._project)
            case FileExtension.UMSBT:
                umsbt = read_umsbt_path(real_path, project=self._project)

                if self._language is None:
                    raise ValueError("No language was provided to map a UMSBT to a MSBT!")

                language_index = None
                for languages in self._config.umsbt_languages.values():
                    if self._language in languages:
                        language_index = languages[self._language]
                        break

                if language_index is None:
                    raise ValueError(f"The language '{self._language}' could not be mapped to a UMSBT!")

                file = umsbt.files[language_index]
            case FileExtension.MSBF:
                file = read_msbf_path(real_path, node_config=self._node_config, project=self._project,
                                      _source_resolver=self)

        self.resolved_cache[os.path.basename(real_path)] = file
        return file

    def retrieve_source_index(self, file: str) -> int:
        extension = FileExtension(Path(file).suffix)
        try:
            return [os.path.basename(file) for file in self._project.sources].index(file.replace(extension, extension.source_format))
        except ValueError as e:
            raise ValueError(f"The source '{file}' could not be mapped to a file in the message root!") from e



