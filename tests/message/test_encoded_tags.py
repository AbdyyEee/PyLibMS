from lms.message.msbtio import read_msbt_path
from lms.message.tag.lms_tag import LMS_EncodedTag
from lms.message.tag.lms_tagexceptions import LMS_TagInvalidFormatError
from tests.message import MSBT_DIRECTORY
from tests.message.msbt_test_util import MSBTTestUtil


class MSBTEncodedTagTests(MSBTTestUtil):

    def test_read_encoded_tags(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "encoded_tag.msbt")

        expected_big_tag = f"[65535:65535 {'-'.join(['FF'] * 0xFFFE)}]"
        expected = {
            "EncodedTagBasicTest00": "[0:0]",
            "EncodedTagBasicTest01": "[0:1]",
            "EncodedTagBasicTest02": "[0:2]",
            "EncodedTagBasicTest03": "[0:3]",
            "EncodedTagBasicTest04": "[0:4]",
            "EncodedTagBasicTest05": "[0:5]",
            "EncodedTagBasicTest06": "[1:0]",
            "EncodedTagBasicTest07": "[2:1]",
            "EncodedTagBasicTest08": "[3:2]",
            "EncodedTagBasicTest09": "[4:3]",
            "EncodedTagBasicTest10": "[5:4]",
            "EncodedTagSingleParameter": "[0:0 00-CD]",
            "EncodedTagTwoParameters": "[0:0 00-00]",
            "EncodedTagThreeByteParameter": "[0:0 00-00-00-CD]",
            "EncodedTagFourByteParameter": "[0:0 00-00-00-00]",
            "EncodedTagMaxValues": "[65535:65535 FF-CD]",
            "EncodedTagBigTag": expected_big_tag,
            "EncodedTagClosing00": "[0:4 FF-FF-FF-FF][/0:4]",
            "EncodedTagClosing01": "[0:1 01-02-03-CD]Test[/0:1]",
            "EncodedAdjacentTags": (
                f"[0:1 50-CD]{expected_big_tag}[0:1 50-CD][65535:65535 FF-CD]"
                "[5:4][65535:65535 FF-CD][0:0 00-00-00-00][65535:65535 FF-CD]"
                f"{expected_big_tag}"
            ),
            "EncodedAdjacentClosingTags": (
                f"[0:1 50-CD][/0:1]{expected_big_tag}"
                "[/65535:65535][0:1 50-CD][/0:1][65535:65535 FF-CD]"
                "[5:4][/5:4][65535:65535 FF-CD][0:0 00-00-00-00][/0:0][38:314 FF-CD]"
                f"{expected_big_tag}[0:0][/0:0][31:3231 FF-CD]"
            ),
        }

        self.assert_messages(msbt, expected)

    def test_edit_encoded_tags(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "encoded_tag.msbt")

        msbt["EncodedTagBasicTest00"].message.tags[0].group_id = 1
        msbt["EncodedTagBasicTest00"].message.tags[0].tag_index = 1
        msbt["EncodedTagSingleParameter"].message.tags[0].parameters = (0xFF,)
        msbt["EncodedTagTwoParameters"].message.tags[0].parameters = (0xFF, 0xFF)
        msbt["EncodedTagThreeByteParameter"].message.tags[0].parameters = (0xFF, 0xFF, 0xFF)
        msbt["EncodedTagFourByteParameter"].message.tags[0].parameters = (0xFF, 0xFF, 0xFF, 0xFF)
        msbt["EncodedTagClosing00"].message.tags[0].parameters = (0x00, 0x00, 0x00, 0x00)
        msbt["EncodedTagClosing00"].message.tags[1].is_closing = False
        msbt["EncodedAdjacentClosingTags"].message.append_encoded_tag(0, 4, 0xFF)
        msbt["EncodedAdjacentClosingTags"].message.append_encoded_tag(0, 4, is_closing=True)
        msbt["EncodedAdjacentClosingTags"].message.append_tag_string("[2:3 FF]")

        expected_big_tag = f"[65535:65535 {'-'.join(['FF'] * 0xFFFE)}]"
        expected = {
            "EncodedTagBasicTest00": "[1:1]",
            "EncodedTagSingleParameter": "[0:0 FF-CD]",
            "EncodedTagTwoParameters": "[0:0 FF-FF]",
            "EncodedTagThreeByteParameter": "[0:0 FF-FF-FF-CD]",
            "EncodedTagFourByteParameter": "[0:0 FF-FF-FF-FF]",
            "EncodedTagClosing00": "[0:4 00-00-00-00][0:4]",
            "EncodedAdjacentClosingTags": (
                f"[0:1 50-CD][/0:1]{expected_big_tag}"
                "[/65535:65535][0:1 50-CD][/0:1][65535:65535 FF-CD]"
                "[5:4][/5:4][65535:65535 FF-CD][0:0 00-00-00-00][/0:0][38:314 FF-CD]"
                f"{expected_big_tag}[0:0][/0:0][31:3231 FF-CD]"
                "[0:4 FF-CD][/0:4][2:3 FF-CD]"
            ),
        }

        written_little, written_big = self.write_little_big_endian(msbt)

        with self.subTest(is_big_endian=False):
            self.assert_messages(written_little, expected)

        with self.subTest(is_big_endian=True):
            self.assert_messages(written_big, expected)

    def test_import_encoded_tags(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "encoded_tag.msbt")

        for entry in msbt:
            for index, tag in enumerate(entry.message.tags):
                with self.subTest(label=entry.name, tag_index=index):
                    self.assertIsInstance(tag, LMS_EncodedTag)

                    text = tag.to_text()
                    from_string = LMS_EncodedTag.from_string(text)

                    self.assertEqual(from_string.group_id, tag.group_id)
                    self.assertEqual(from_string.tag_index, tag.tag_index)
                    self.assertEqual(from_string.parameters, tag.parameters)
                    self.assertEqual(from_string.is_closing, tag.is_closing)
                    self.assertEqual(from_string.to_text(), text)

    def test_invalid_encoded_tag_formats(self) -> None:
        invalid_tags = (
            "[0:1 F]",
            "[0:1 GG]",
            "[0:1 00 FF]",
            "[0:1 00--FF]",
            "[0:1 00-FF-]",
            "[-1:0]",
            "[0:-1]",
            "[0:]",
            "[0:1",
        )

        for text in invalid_tags:
            with self.subTest(text=text):
                with self.assertRaises(LMS_TagInvalidFormatError):
                    LMS_EncodedTag.from_string(text)
