from lms.message.msbt import MSBT
from lms.message.umsbt import UMSBT
from lms.message.umsbtio import read_umsbt_path, write_umsbt, read_umsbt
from tests.message import UMSBT_DIRECTORY
from tests.message.msbt_test_util import MSBTTestUtil


class TestUMSBTCases(MSBTTestUtil):

    def test_read_simple_umsbt(self) -> None:
        umsbt = read_umsbt_path(UMSBT_DIRECTORY / "simple.umsbt")

        expected = [
            {"UMsbtFile00Label00": "UMSBT Message 00", "UMsbtFile00Label01": "UMSBT Message 01"},
            {"UMsbtFile01Label00": "UMSBT Message 02", "UMsbtFile01Label01": "UMSBT Message 03"},
            {"UMsbtFile02Label00": "UMSBT Message 04", "UMsbtFile02Label01": "UMSBT Message 05"},
            {"UMsbtFile03Label00": "UMSBT Message 06", "UMsbtFile03Label01": "UMSBT Message 07"}
        ]

        self.assertEqual(len(umsbt), len(expected))

        self.assert_archive_messages(umsbt, expected)

    def test_new_umsbt(self) -> None:
        umsbt = UMSBT()

    def test_add_msbt(self) -> None:
        umsbt = read_umsbt_path(UMSBT_DIRECTORY / "simple.umsbt")

        msbt = MSBT.new()
        msbt.create_entry("UMsbtFile04Label00", "UMSBT Message 08")
        msbt.create_entry("UMsbtFile04Label01", "UMSBT Message 09")
        umsbt.add_msbt(msbt)

        expected = [
            {"UMsbtFile00Label00": "UMSBT Message 00", "UMsbtFile00Label01": "UMSBT Message 01"},
            {"UMsbtFile01Label00": "UMSBT Message 02", "UMsbtFile01Label01": "UMSBT Message 03"},
            {"UMsbtFile02Label00": "UMSBT Message 04", "UMsbtFile02Label01": "UMSBT Message 05"},
            {"UMsbtFile03Label00": "UMSBT Message 06", "UMsbtFile03Label01": "UMSBT Message 07"},
            {"UMsbtFile04Label00": "UMSBT Message 08", "UMsbtFile04Label01": "UMSBT Message 09"}
        ]

        self.assert_archive_messages(read_umsbt(write_umsbt(umsbt)), expected)

    def test_insert_msbt(self) -> None:
        umsbt = read_umsbt_path(UMSBT_DIRECTORY / "simple.umsbt")

        msbt = MSBT.new()
        msbt.create_entry("InsertedFileLabel", "UMSBT File Inserted Message")
        umsbt.insert_msbt(1, msbt)

        expected = [
            {"UMsbtFile00Label00": "UMSBT Message 00", "UMsbtFile00Label01": "UMSBT Message 01"},
            {"InsertedFileLabel": "UMSBT File Inserted Message"},
            {"UMsbtFile01Label00": "UMSBT Message 02", "UMsbtFile01Label01": "UMSBT Message 03"},
            {"UMsbtFile02Label00": "UMSBT Message 04", "UMsbtFile02Label01": "UMSBT Message 05"},
            {"UMsbtFile03Label00": "UMSBT Message 06", "UMsbtFile03Label01": "UMSBT Message 07"}
        ]

        self.assert_archive_messages(read_umsbt(write_umsbt(umsbt)), expected)
