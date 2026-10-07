from dataclasses import dataclass

from lms.fileio.encoding import FileEncoding
from lms.fileio.io import FileEndian


@dataclass
class LMS_FileInfo:
    endian: FileEndian = FileEndian.LITTLE
    encoding: FileEncoding = FileEncoding.UTF16
    version: int = 3
    section_count: int = 2
