import unittest

from lms.common.field.lms_datatype import LMS_DataType
from lms.fileio.encoding import FileEncoding
from lms.fileio.endian import FileEndian
from lms.message.lms_messagetext import LMS_MessageText
from lms.message.msbt import MSBT, MSBTSection
from lms.message.msbtio import write_msbt, read_msbt
from lms.message.tag.lms_tag import LMS_EncodedTag, LMS_DecodedTag
from lms.titleconfig.config import TitleConfig
from lms.titleconfig.definitions.color import Color
from lms.titleconfig.definitions.project import Project
from lms.titleconfig.definitions.tags import TagConfig, TagDefinition

config = TitleConfig(
    "Test",
    projects={"global": (project := Project(name="global"))},
)

project.add_color(Color.from_dict({"name": "Color00", "red": 0xFF, "green": 0xFF, "blue": 0xFF, "alpha": 0xFF}))
project.add_color(Color.from_dict({"name": "Color01", "red": 0x00, "green": 0x33, "blue": 0x00, "alpha": 0xFF}))
project.set_tag_config(tag_config := TagConfig(
    group_map := {0: "UnsignedTags", 1: "SignedTags", 2: "MiscTags"}
))

tag_definitions = [
    {
        "name": "UInt8",
        "group_id": 0,
        "tag_index": 1,
        "parameters": [
            {"name": "value", "datatype": "u8"}
        ]
    },
    {
        "name": "UInt16",
        "group_id": 0,
        "tag_index": 2,
        "parameters": [
            {"name": "value", "datatype": "u16"}
        ]
    },
    {
        "name": "UInt32",
        "group_id": 0,
        "tag_index": 3,
        "parameters": [
            {"name": "value", "datatype": "u32"}
        ]
    },
    {
        "name": "Int8",
        "group_id": 1,
        "tag_index": 0,
        "parameters": [
            {"name": "value", "datatype": "i8"}
        ]
    },    {
        "name": "Int32",
        "group_id": 1,
        "tag_index": 2,
        "parameters": [
            {"name": "value", "datatype": "i16"}
        ]
    },
    {
        "name": "Int32",
        "group_id": 1,
        "tag_index": 3,
        "parameters": [
            {"name": "value", "datatype": "i32"}
        ]
    },
]

for definition in tag_definitions:
    tag_config.add_definition(TagDefinition.from_dict(definition, group_map))


class TestMSBT(unittest.TestCase):

    def assertFileOneToOne(self, msbt: MSBT) -> MSBT:
        self.assertEqual(data := write_msbt(msbt), write_msbt(written := read_msbt(data)))
        return written

    def test_basic(self) -> None:
        for msbt in [MSBT.new(),
                     MSBT.new(encoding=FileEncoding.UTF8),
                     MSBT.new(endian=FileEndian.BIG),
                     MSBT.new(endian=FileEndian.BIG, encoding=FileEncoding.UTF8)]:
            with self.subTest(endian=msbt.info.endian, encoding=msbt.info.encoding):
                msbt.create_entry("Entry00", message="First entry")
                msbt.create_entry("Entry01", message="Second entry")
                self.assertFileOneToOne(msbt)

    def test_serialization(self) -> None:
        msbt = MSBT.new()
        msbt.create_entry("Entry00", message="First entry")
        msbt.create_entry("Entry01", message="Second entry")

        with self.subTest(serialization_type="dict"):
            self.assertFileOneToOne(MSBT.from_dict(msbt.to_dict()))

        with self.subTest(serialization_type="json"):
            self.assertFileOneToOne(MSBT.from_json(msbt.to_json()))

        with self.subTest(serialization_type="yaml"):
            self.assertFileOneToOne(MSBT.from_yaml(msbt.to_yaml()))

    def test_message_edits(self) -> None:
        msbt = MSBT.new()
        msbt.create_entry("Entry00", message="First entry")
        msbt.create_entry("Entry01", message="Second entry")
        msbt[0].message.message = "Edited Entry 1"
        msbt[1].message.message = "Edited Entry 2"
        self.assertTrue(msbt[0].message != "First entry")
        self.assertTrue(msbt[1].message != "Second entry")
        self.assertFileOneToOne(msbt)

    # Non-config related tests
    def test_encoded_attributes(self) -> None:
        msbt = MSBT.new(size_per_attribute=2)
        msbt.create_entry("Entry00", message="First entry", attribute=b"\x00\x00")
        msbt.create_entry("Entry01", message="Second entry", attribute=b"\x00\x00")

        written_msbt = self.assertFileOneToOne(msbt)
        for entry in written_msbt:
            with self.subTest(entry=entry.name):
                self.assertEqual(entry.attribute, b"\x00\x00")

    def test_encoded_tags(self) -> None:
        msbt = MSBT.new()
        msbt.create_entry("Entry00", message="First [0:4][1:3 33-33-FF-FF][21:234 00]entry")
        self.assertEqual(len(msbt[0].message.tags), 3)

        tag_1 = msbt[0].message.tags[0]
        tag_2 = msbt[0].message.tags[1]
        tag_3 = msbt[0].message.tags[2]

        tags = [tag_1, tag_2, tag_3]
        tag_strings = ['[0:4]', '[1:3 33-33-FF-FF]', '[21:234 00-CD]']
        expected_parameters = [(), (0x33, 0x33, 0xFF, 0xFF), (0x00, 0xCD)]

        for i, tag in enumerate(tags):
            tag_string = tag_strings[i]
            with self.subTest(tag=tag_string):
                self.assertEqual(tag.parameters, expected_parameters[i])
                self.assertEqual(LMS_EncodedTag.from_string(tag_string).to_text(), tag_string)

        self.assertFileOneToOne(msbt)

        for tag_obj, new_group_id, new_tag_index, new_parameters, tag_string in zip([tag_1, tag_2, tag_3],
                                                                                    [0x01, 0x00, 0xFF],
                                                                                    [0xFF, 0x02, 0xFF],
                                                                                    [(0xFF, 0xCD), (),
                                                                                    (0xFF, 0xFF, 0xFF, 0xFF, 0x00,
                                                                                     0x00)],
                                                                                    ["[0:255 FF-CD]", "[0:2]",
                                                                                     "[255:255 FF-FF-FF-FF-00-00]"]):
            with self.subTest(tag=tag_obj.to_text()):
                tag_obj.group_id = new_group_id
                tag_obj.tag_index = new_tag_index
                tag_obj.parameters = new_parameters
                self.assertEqual(LMS_EncodedTag.from_string(tag_string).to_text(), tag_string)


        tag_1.group_id = 0x01
        tag_2.group_id = 0x00
        tag_3.group_id = 0xFF

        self.assertFileOneToOne(msbt)

    def test_style_indexes(self) -> None:
        msbt = MSBT.new()
        msbt.create_entry("Entry00", message="First Entry", style_index=0)
        self.assertEqual(msbt[0].style_index, 0)
        msbt[0].style_index = 1
        self.assertEqual(msbt[0].style_index, 1)
        self.assertTrue(msbt.section_exists(MSBTSection.TSY1))
        self.assertFileOneToOne(msbt)

    # Configuration based
    def test_decoded_tags(self) -> None:
        msbt = MSBT.new(project=config.global_project)

        # Unsigned tests
        msbt.create_entry("UInt8Tag", message=f'[UnsignedTags:UInt8 value="{0xFF}"]')
        msbt.create_entry("UInt16Tag", message=f'[UnsignedTags:UInt16 value="{0xFFFF}"]')
        msbt.create_entry("UInt32Tag", message=f'[UnsignedTags:UInt32 value="{0xFFFFFFFF}"]')

        self.assertFileOneToOne(msbt)

        tag_1 = msbt[0].message.tags[0]
        tag_2 = msbt[1].message.tags[0]
        tag_3 = msbt[2].message.tags[0]

        tags = [tag_1, tag_2, tag_3]
        tag_strings = [
            f'[UnsignedTags:UInt8 value="{0xFF}"]',
            f'[UnsignedTags:UInt16 value="{0xFFFF}"]',
            f'[UnsignedTags:UInt32 value="{0xFFFFFFFF}"]',
            ]

        expected_parameters = [0xFF, 0xFFFF, 0xFFFFFFFF]

        for i, tag in enumerate(tags):
            tag_string = tag_strings[i]
            with self.subTest(tag=tag_string):
                self.assertEqual(tag.parameters["value"].value, expected_parameters[i])
                self.assertEqual(LMS_DecodedTag.from_string(tag_string, project.tag_config).to_text(), tag_string)

        added = msbt[0].message.append_decoded_tag("UnsignedTags", "UInt32", value=0)
        self.assertEqual(len(msbt[0].message.tags), 2)
        self.assertEqual(added.to_text(), f'[UnsignedTags:UInt32 value="0"]')

        self.assertFileOneToOne(msbt)