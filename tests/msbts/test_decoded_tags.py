from lms.message.msbtio import read_msbt_path
from lms.message.tag.lms_tag import LMS_DecodedTag
from lms.message.tag.lms_tagexceptions import LMS_TagInvalidFormatError
from lms.titleconfig.config import TitleConfig
from tests.msbts import MSBT_DIRECTORY
from tests.msbts.msbt_test_util import MSBTTestUtil

TAG_CONFIG = TitleConfig.load_config({
    "tag_definitions": {
        "groups": {0: "test"},
        "tags": [
            {
                "name": "uint8",
                "group_id": 0,
                "tag_index": 0,
                "parameters": [{"name": "value", "datatype": "uint8"}],
            },
            {
                "name": "uint16",
                "group_id": 0,
                "tag_index": 1,
                "parameters": [{"name": "value", "datatype": "uint16"}],
            },
            {
                "name": "uint32",
                "group_id": 0,
                "tag_index": 2,
                "parameters": [{"name": "value", "datatype": "uint32"}],
            },
            {
                "name": "int8",
                "group_id": 0,
                "tag_index": 3,
                "parameters": [{"name": "value", "datatype": "int8"}],
            },
            {
                "name": "int16",
                "group_id": 0,
                "tag_index": 4,
                "parameters": [{"name": "value", "datatype": "int16"}],
            },
            {
                "name": "int32",
                "group_id": 0,
                "tag_index": 5,
                "parameters": [{"name": "value", "datatype": "int32"}],
            },
            {
                "name": "float32",
                "group_id": 0,
                "tag_index": 6,
                "parameters": [{"name": "value", "datatype": "float32"}],
            },
            {
                "name": "string",
                "group_id": 0,
                "tag_index": 7,
                "parameters": [{"name": "value", "datatype": "string"}],
            },
            {
                "name": "enum",
                "group_id": 0,
                "tag_index": 8,
                "parameters": [{
                    "name": "value",
                    "datatype": "enum",
                    "enum_members": {0: "Normal", 1: "Special"},
                }],
            },
            {
                "name": "bool",
                "group_id": 0,
                "tag_index": 9,
                "parameters": [{"name": "value", "datatype": "bool"}],
            },
            {
                "name": "none",
                "group_id": 0,
                "tag_index": 10,
                "parameters": [],
            },
        ],
    },
}).tag_config


class MSBTDecodedTagTests(MSBTTestUtil):

    def test_read_decoded_tags(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "decoded_tag.msbt", tag_config=TAG_CONFIG)
        self.assertEqual(len(msbt), 11)

        expected = {
            "Uint8Tag": f'[test:uint8 value="{0xFF}"]',
            "Uint16Tag": f'[test:uint16 value="{0xFFFF}"]',
            "Uint32Tag": f'[test:uint32 value="{0xFFFFFFFF}"]',
            "Int8Tag": f'[test:int8 value="{-0x80}"]',
            "Int16Tag": f'[test:int16 value="{-0x8000}"]',
            "Int32Tag": f'[test:int32 value="{-0x80000000}"]',
            "Float32Tag": '[test:float32 value="1.5"]',
            "StringTag": '[test:string value="Test"]',
            "EnumTag": '[test:enum value="Special"]',
            "BooleanTag": '[test:bool value="True"]',
            "MultiTagTest": '[test:none]Test[/test:none]After',
        }

        self.assert_messages(msbt, expected)

    def test_import_decoded_tags(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "decoded_tag.msbt", tag_config=TAG_CONFIG)
        self.assertEqual(len(msbt), 11)

        for entry in msbt:
            for i, tag in enumerate(entry.message.tags):
                with self.subTest(label=entry.name, tag_index=i):
                    self.assertIsInstance(tag, LMS_DecodedTag)

                    text = tag.to_text()
                    from_string = LMS_DecodedTag.from_string(text, TAG_CONFIG)

                    self.assertEqual(from_string.group_id, tag.group_id)
                    self.assertEqual(from_string.tag_index, tag.tag_index)
                    self.assertEqual(from_string.group_name, tag.group_name)
                    self.assertEqual(from_string.tag_name, tag.tag_name)
                    self.assertEqual(from_string.description, tag.description)

                    # Can't check equality with the LMS_FieldMap directly since from_string will create a new object
                    if tag.parameters:
                        self.assertEqual(from_string.parameters.to_dict(), tag.parameters.to_dict())

                    self.assertEqual(from_string.is_closing, tag.is_closing)
                    self.assertEqual(from_string.to_text(), text)

    def test_edit_decoded_tags(self) -> None:
        msbt = read_msbt_path(MSBT_DIRECTORY / "decoded_tag.msbt", tag_config=TAG_CONFIG)
        self.assertEqual(len(msbt), 11)

        msbt["Uint8Tag"].message.tags[0].parameters["value"] = 0x12
        msbt["Uint16Tag"].message.tags[0].parameters["value"] = 0x1234
        msbt["Uint32Tag"].message.tags[0].parameters["value"] = 0x12345678
        msbt["Int8Tag"].message.tags[0].parameters["value"] = -0x12
        msbt["Int16Tag"].message.tags[0].parameters["value"] = -0x1234
        msbt["Int32Tag"].message.tags[0].parameters["value"] = -0x12345678
        msbt["Float32Tag"].message.tags[0].parameters["value"] = 50.25
        msbt["StringTag"].message.tags[0].parameters["value"] = "NewTest"
        msbt["EnumTag"].message.tags[0].parameters["value"] = "Normal"
        msbt["BooleanTag"].message.tags[0].parameters["value"] = False
        msbt["MultiTagTest"].message.text = (
            '[test:none]Test[/test:none]After[test:none]Before[/test:none]Test'
        )
        msbt["MultiTagTest"].message.append_decoded_tag("test", "none")
        msbt["MultiTagTest"].message.append_decoded_tag("test", "none", is_closing=True)
        msbt["MultiTagTest"].message.append_decoded_tag("test", "uint16", value=0xFFFF)
        msbt["MultiTagTest"].message.append_tag_string('[test:string value="TagString"]')
        msbt["MultiTagTest"].message.append_decoded_tag("test", "none")
        msbt["MultiTagTest"].message.append_decoded_tag("test", "none")
        msbt["MultiTagTest"].message.append_decoded_tag("test", "none")
        msbt["MultiTagTest"].message.append_decoded_tag("test", "uint8", value=0xFF)
        msbt["MultiTagTest"].message.append_decoded_tag("test", "uint16", value=0xFFFF)
        msbt["MultiTagTest"].message.append_decoded_tag("test", "uint32", value=0xFFFFFFFF)

        expected = {
            "Uint8Tag": f'[test:uint8 value="{0x12}"]',
            "Uint16Tag": f'[test:uint16 value="{0x1234}"]',
            "Uint32Tag": f'[test:uint32 value="{0x12345678}"]',
            "Int8Tag": f'[test:int8 value="{-0x12}"]',
            "Int16Tag": f'[test:int16 value="{-0x1234}"]',
            "Int32Tag": f'[test:int32 value="{-0x12345678}"]',
            "Float32Tag": '[test:float32 value="50.25"]',
            "StringTag": '[test:string value="NewTest"]',
            "EnumTag": '[test:enum value="Normal"]',
            "BooleanTag": '[test:bool value="False"]',
            "MultiTagTest": (
                '[test:none]Test[/test:none]After[test:none]Before[/test:none]Test'
                '[test:none][/test:none]'
                f'[test:uint16 value="{0xFFFF}"]'
                '[test:string value="TagString"]'
                '[test:none][test:none][test:none]'
                f'[test:uint8 value="{0xFF}"]'
                f'[test:uint16 value="{0xFFFF}"]'
                f'[test:uint32 value="{0xFFFFFFFF}"]'
            ),
        }

        written_little, written_big = self.write_little_big_endian(msbt, tag_config=TAG_CONFIG)

        with self.subTest(is_big_endian=False):
            self.assert_messages(written_little, expected)

        with self.subTest(is_big_endian=True):
            self.assert_messages(written_big, expected)

    def test_invalid_parameter_inputs(self) -> None:
        msbt = read_msbt_path(
            MSBT_DIRECTORY / "decoded_tag.msbt",
            tag_config=TAG_CONFIG,
        )

        invalid_values = (
            ("Uint8Tag", -1),
            ("Uint8Tag", 0xFFF),
            ("Int8Tag", -129),
            ("Int8Tag", 128),
            ("Int16Tag", 0xFFFF),
            ("Int32Tag", 0x80000000),
            ("EnumTag", "MissingMember"),
        )

        for label, value in invalid_values:
            with self.subTest(label=label, value=value):
                parameters = msbt[label].message.tags[0].parameters
                previous = parameters["value"].value

                with self.assertRaises(ValueError):
                    parameters["value"] = value

                self.assertEqual(parameters["value"].value, previous)

    def test_invalid_decoded_tag_formats(self) -> None:
        invalid_tags = (
            "[test:uint8",
            "[test:]",
            "[:uint8]",
            "[test::uint8]",
            "[test/uint8]",
            "[0:uint8]",
            "[test:0uint8]",
            "test:uint8]",
            "[//test:none]",
        )

        for text in invalid_tags:
            with self.subTest(text=text):
                with self.assertRaises(LMS_TagInvalidFormatError):
                    LMS_DecodedTag.from_string(text, TAG_CONFIG)
