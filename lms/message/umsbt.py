from types import MappingProxyType
from typing import overload, Mapping, Sequence, Iterator

from lms.message.msbt import MSBT


class UMSBT:
    """Class that represents a UMSBT file, an archive for MSBT files."""

    def __init__(self, files: Sequence[MSBT] | None = None) -> None:
        self._files = list(files) if files is not None else []

        for file in self._files:
            if not isinstance(file, MSBT):
                raise TypeError("Only MSBTs are allowed for UMSBT archives!")

        self._realign_filenames()

    @overload
    def __getitem__(self, index: int) -> MSBT:
        ...

    @overload
    def __getitem__(self, label: str) -> MSBT:
        ...

    def __getitem__(self, value: int | str) -> MSBT:
        if isinstance(value, str):
            return self.file_map[value]

        return self._files[value]

    def __len__(self) -> int:
        return len(self._files)

    def __iter__(self) -> Iterator[MSBT]:
        return iter(self._files)

    @property
    def files(self) -> tuple[MSBT, ...]:
        """Maps of files tied to this instance."""
        return tuple(self._files)

    @property
    def file_map(self) -> Mapping[str, MSBT]:
        """Maps of files tied to this instance."""
        return MappingProxyType({msbt.filename: msbt for msbt in self._files})

    def add_msbt(self, msbt: MSBT) -> None:
        """
        Adds a MSBT to the UMSBT archive.

        :param msbt: the msbt to add.
        """
        self._files.append(msbt)
        self._realign_filenames()

    def insert_msbt(self, position: int, msbt: MSBT) -> None:
        """
        Inserts a MSBT in the archive at a specific index

        :param position: position of the MSBT to insert.
        :param msbt: the msbt to insert.
        """
        self._files.insert(position, msbt)
        self._realign_filenames()

    @overload
    def remove_msbt(self, msbt: MSBT) -> None:
        ...

    @overload
    def remove_msbt(self, msbt: int) -> None:
        ...

    def remove_msbt(self, msbt: MSBT | int) -> None:
        """
        Deletes a MSBT from the UMSBT archive.

        :param msbt: the msbt object or index to remove.
        """
        if isinstance(msbt, MSBT):
            self._files.remove(msbt)
        else:
            del self._files[msbt]

        self._realign_filenames()

    def _realign_filenames(self) -> None:
        for i, msbt in enumerate(self._files):
            msbt.filename = f"{i}.msbt"
