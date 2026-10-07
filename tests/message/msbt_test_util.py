import unittest
from collections.abc import Mapping
from typing import Any, Sequence

from lms.fileio.endian import FileEndian
from lms.message.msbt import MSBT
from lms.message.msbtio import read_msbt, write_msbt
from lms.message.umsbt import UMSBT


class MSBTTestUtil(unittest.TestCase):

    def assert_messages(self, msbt: MSBT, expected: Mapping[str, str]) -> None:
        for label, text in expected.items():
            with self.subTest(label=label):
                self.assertEqual(msbt[label].message.text, text)

    def assert_archive_messages(self, umsbt: UMSBT, expected: Sequence[Mapping[str, str]]) -> None:
        self.assertEqual(len(umsbt), len(expected))

        for i, msbt in enumerate(umsbt):
            with self.subTest(filename=msbt.filename):
                self.assertEqual(msbt.filename, f"{i}.msbt")
                self.assertEqual(len(msbt), len(expected[i]))
                self.assert_messages(msbt, expected[i])

    def write_little_big_endian(self, msbt: MSBT, **read_options: Any) -> tuple[MSBT, MSBT]:
        original_endian = msbt.info.endian
        try:
            msbt.info.endian = FileEndian.LITTLE
            restored_little = read_msbt(write_msbt(msbt), **read_options)
            msbt.info.endian = FileEndian.BIG
            restored_big = read_msbt(write_msbt(msbt), **read_options)
            return restored_little, restored_big
        finally:
            msbt.info.endian = original_endian
