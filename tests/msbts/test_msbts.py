from tests.msbts import MSBT_DIRECTORY
from tests.msbts.msbt_test_util import MSBTTestUtil

from lms.fileio.encoding import FileEncoding
from lms.message.msbtio import read_msbt_path


class TestMSBTCases(MSBTTestUtil):

    def test_read_simple(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "simple.msbt")
        self.assertEqual(len(msbt), 4)
        self.assertEqual(msbt.info.encoding, FileEncoding.UTF16)

        expected = {
            "Test00": "Test Message 00",
            "Test01": "Test Message 01",
            "Test02": "Test Message 02",
            "Test03": "Test Message 03",
        }

        self.assert_messages(msbt, expected)

    def test_read_example_utf8(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "example_utf8.msbt")
        self.assertEqual(len(msbt), 4)
        self.assertEqual(msbt.info.encoding, FileEncoding.UTF8)

        expected = {
            "Test00": "Test Message 00",
            "Test01": "Test Message 01",
            "Test02": "Test Message 02",
            "Test03": "Test Message 03",
        }

        self.assert_messages(msbt, expected)

    def test_read_example_utf16(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "example_utf16.msbt")

        expected = {
            "TestUTF16English": "Test",
            "TestUTF16German": "Test ÄÖÜß",
            "TestUTF16French": "Test éèêç",
            "TestUTF16Japanese": "Test テスト",
            "TestUTF16Chinese": "Test 测试",
            "TestUTF16Korean": "Test 테스트",
            "TestUTF16Arabic": "Test اختبار",
            "TestUTF16Russian": "Test Тест",
            "TestUTF16Combining": "Test e\u0301",
        }

        written_little, written_big = self.write_little_big_endian(msbt)

        self.assertEqual(len(written_little), len(msbt))
        self.assertEqual(len(written_big), len(msbt))
        self.assert_messages(written_little, expected)

    def test_simple_msbt_edits(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "simple.msbt")

        expected = {
            "Test00": "Message Test 00",
            "Test01": "Message Test 01",
            "Test02": "Message Test 02",
            "Test03": "Message Test 03",
        }

        for label, text in expected.items():
            msbt[label].message.text = text

        written_little, written_big = self.write_little_big_endian(msbt)

        self.assertEqual(len(written_little), len(msbt))
        self.assertEqual(len(written_big), len(msbt))

        with self.subTest(is_big_endian=False):
            self.assert_messages(written_little, expected)

        with self.subTest(is_big_endian=True):
            self.assert_messages(written_big, expected)

    def test_nl1(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "nli1.msbt")
        self.assertEqual(len(msbt), 4)

        expected = {
            "0": "NL1 Test 00",
            "1": "NL1 Test 01",
            "2": "NL1 Test 02",
            "3": "NL1 Test 03",
        }

        written_little, written_big = self.write_little_big_endian(msbt)

        with self.subTest(is_big_endian=False):
            self.assert_messages(written_little, expected)

        with self.subTest(is_big_endian=True):
            self.assert_messages(written_big, expected)
