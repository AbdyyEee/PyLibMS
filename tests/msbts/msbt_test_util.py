"""Shared setup and assertions for MSBT tests."""

import unittest
from collections.abc import Mapping
from typing import Any

from lms.message.msbt import MSBT
from lms.message.msbtentry import MSBTEntry
from lms.message.msbtio import read_msbt, write_msbt


class MSBTTestUtil(unittest.TestCase):

    def assert_messages(self, msbt: MSBT, expected: Mapping[str, str]) -> None:
        for label, text in expected.items():
            with self.subTest(label=label):
                self.assertEqual(msbt[label].message.text, text)

    def create_msbt(self, messages: Mapping[str, str], **options: Any) -> MSBT:
        msbt = MSBT.new(**options)
        for label, text in messages.items():
            msbt.add_entry(MSBTEntry(label, message=text))
        return msbt

    def write_little_big_endian(self, msbt: MSBT, **read_options: Any) -> tuple[MSBT, MSBT]:
        original_endian = msbt.info.is_big_endian
        try:
            msbt.info.is_big_endian = False
            restored_little = read_msbt(write_msbt(msbt), **read_options)
            msbt.info.is_big_endian = True
            restored_big = read_msbt(write_msbt(msbt), **read_options)
            return restored_little, restored_big
        finally:
            msbt.info.is_big_endian = original_endian
