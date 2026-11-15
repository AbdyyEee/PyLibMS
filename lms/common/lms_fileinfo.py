from dataclasses import dataclass

from lms.common.lms_constants import LMS_MINIMUM_VERSION
from lms.fileio.encoding import FileEncoding
from lms.fileio.io import FileEndian


@dataclass
class LMS_FileInfo:
    endian: FileEndian = FileEndian.LITTLE
    encoding: FileEncoding = FileEncoding.UTF16
    version: int = LMS_MINIMUM_VERSION
    section_count: int = 2

    def to_dict(self):
        return {
            "endian": self.endian.value,
            "encoding": self.encoding.value,
            "version": self.version,
            "section_count": self.section_count,
        }
