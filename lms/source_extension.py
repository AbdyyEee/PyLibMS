from enum import StrEnum
from typing import Literal


class FileExtension(StrEnum):
    MSBT = ".msbt"
    UMSBT = ".umsbt"
    MSBF = ".msbf"

    @property
    def source_format(self) -> Literal[".mstxt", ".msflow"]:
        return {
            self.MSBT: ".mstxt",
            self.UMSBT: ".mstxt",
            self.MSBF: ".msflow",
        }[self]