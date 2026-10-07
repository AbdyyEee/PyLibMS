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
        msbt_0 = MSBT.new()

        msbt_0.create_entry("UMsbtFile00Label00", message="UMSBT Message 00")
        msbt_0.create_entry("UMsbtFile00Label01", message="UMSBT Message 01")

        msbt_1 = MSBT.new()

        msbt_1.create_entry("UMsbtFile01Label00", message="UMSBT Message 02")
        msbt_1.create_entry("UMsbtFile01Label01", message="UMSBT Message 03")

        msbt_2 = MSBT.new()
        msbt_2.create_entry("UMsbtFile02Label00", message="UMSBT Message 04")
        msbt_2.create_entry("UMsbtFile02Label01", message="UMSBT Message 05")

        msbt_3 = MSBT.new()
        msbt_3.create_entry("UMsbtFile03Label00", message="UMSBT Message 06")
        msbt_3.create_entry("UMsbtFile03Label01", message="UMSBT Message 07")

        umsbt = UMSBT([msbt_0, msbt_1, msbt_2, msbt_3])

        expected = [
            {"UMsbtFile00Label00": "UMSBT Message 00", "UMsbtFile00Label01": "UMSBT Message 01"},
            {"UMsbtFile01Label00": "UMSBT Message 02", "UMsbtFile01Label01": "UMSBT Message 03"},
            {"UMsbtFile02Label00": "UMSBT Message 04", "UMsbtFile02Label01": "UMSBT Message 05"},
            {"UMsbtFile03Label00": "UMSBT Message 06", "UMsbtFile03Label01": "UMSBT Message 07"}
        ]

        self.assertEqual(list(umsbt), [msbt_0, msbt_1, msbt_2, msbt_3])

        self.assert_archive_messages(UMSBT(), [])
        self.assert_archive_messages(read_umsbt(write_umsbt(umsbt)), expected)

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
