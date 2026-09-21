import re
from typing import TypeGuard

from lms.common.field.lms_field import LMS_FieldMap
from lms.message.tag.lms_tagexceptions import (
    LMS_TagInvalidFormatError,
    LMS_TagForbiddenParametersError,
)
from lms.titleconfig.definitions.tags import TagConfig, TagDefinition

TAG_PADDING_VALUE = 0xCD


class LMS_EncodedTag:
    """
    A class that represents an encoded tag.
    """

    TAG_FORMAT = re.compile(r"\[\s*(/)?\s*(\d+)\s*:\s*(\d+)[^]]*]")
    PARAMETER_FORMAT = re.compile(r"^\s*([0-9A-Fa-f]{2})(\s*-\s*[0-9A-Fa-f]{2})*\s*$")

    def __init__(
        self,
        group_id: int,
        tag_index: int,
        parameters: list[int] | None = None,
        is_fallback: bool = False,
        is_closing: bool = False,
    ):
        self._group_id = group_id
        self._tag_index = tag_index
        self._parameters = parameters

        self._is_fallback = is_fallback
        self._is_closing = is_closing

    def __len__(self) -> int:
        return len(self.to_text())

    @property
    def group_id(self) -> int:
        """The group id for the tag."""
        return self._group_id

    @property
    def tag_index(self) -> int:
        """The tag index in the tags group."""
        return self._tag_index

    @property
    def parameters(self) -> list[int] | None:
        """The list of parameters."""
        return self._parameters

    @property
    def is_fallback(self) -> bool:
        """Determines if the tag is a fallback tag. Fallback tags have a '!' prefix before the group index."""
        return self._is_fallback

    @property
    def is_closing(self) -> bool:
        """Determines if the tag is a closing tag."""
        return self._is_closing

    def to_text(self) -> str:
        if self._is_closing:
            return f"[/{self._group_id}:{self._tag_index}]"

        fallback_prefix = "!" if self._is_fallback else ""

        if self._parameters is None:
            return f"[{self.group_id}:{self.tag_index}]"

        # 02x format to convert any int to hexadecimal uppercase
        parameters = "-".join(
            format(param, "02x").upper() for param in self._parameters
        )
        return f"[{fallback_prefix}{self.group_id}:{self.tag_index} {parameters}]"

    @classmethod
    def from_string(cls, tag: str):
        if not (match := cls.TAG_FORMAT.match(tag)):
            raise LMS_TagInvalidFormatError(
                f"Invalid encoded tag format detected for tag: '{tag}'"
            )

        is_closing = match.group(1) is not None
        group_id, tag_index = match.group(2), match.group(3)

        if not group_id.isdigit() or not tag_index.isdigit():
            raise LMS_TagInvalidFormatError(
                f"The group id and or tag index must be digits in tag: '{tag}'"
            )

        group_id, tag_index = int(group_id), int(tag_index)
        param_str = tag[match.end(3) :].strip().removesuffix("]").strip()

        if is_closing:
            if param_str:
                raise LMS_TagForbiddenParametersError(
                    "There may not be parameters for closing tags!"
                )

            return cls(group_id, tag_index, is_closing=True)

        if not param_str:
            return cls(group_id, tag_index)

        if not cls.PARAMETER_FORMAT.match(param_str):
            raise LMS_TagInvalidFormatError(
                f"Malformed parameters in the tag '{tag}'. Ensure all parameters are separated by dashes."
            )

        try:
            parameters = [
                int(param.strip().upper(), 16) for param in param_str.split("-")
            ]
        except ValueError:
            raise LMS_TagInvalidFormatError(
                f"Malformed parameters in tag '{tag}'. Ensure all the parameters are integers."
            )

        if len(parameters) % 2 == 1:
            parameters.append(TAG_PADDING_VALUE)

        return cls(group_id, tag_index, parameters)


class LMS_DecodedTag:
    """
    A class that represents a decoded tag.
    """

    TAG_FORMAT = re.compile(
        r"\[\s*(/)?\s*([A-Za-z]\w*)\s*:\s*([A-Za-z]+)(?:\s+[^]]*)?\s*]"
    )
    PARAMETER_FORMAT = re.compile(r'(\w+)="([^"]*)"')

    def __init__(
        self,
        definition: TagDefinition,
        parameters: LMS_FieldMap | None = None,
        is_closing: bool = False,
    ):
        self._definition = definition
        self._parameters = parameters

        self._is_closing = is_closing

    def __len__(self) -> int:
        return len(self.to_text())

    @property
    def group_id(self) -> int:
        """The group id for the tag."""
        return self._definition.group_id

    @property
    def tag_index(self) -> int:
        """The tag index in the tags group."""
        return self._definition.tag_index

    @property
    def group_name(self) -> str:
        """The name of the tag group."""
        return self._definition.group_name

    @property
    def tag_name(self) -> str:
        """The name of the tag in the tag group."""
        return self._definition.tag_name

    @property
    def description(self) -> str:
        """The description of the tag."""
        return self._definition.description

    @property
    def is_closing(self) -> bool:
        """Determines if the tag is a closing tag."""
        return self._is_closing

    @property
    def parameters(self) -> LMS_FieldMap | None:
        """The map of parameters for the tag."""
        return self._parameters

    def to_text(self) -> str:
        if self._is_closing:
            return f"[/{self._definition.group_name}:{self._definition.tag_name}]"

        if not self._parameters:
            return f"[{self._definition.group_name}:{self._definition.tag_name}]"

        parameters = []
        for param in self._parameters:
            if isinstance(param.value, bytes):
                parameters.append(f'{param.name}="{param.value.hex()}"')
            else:
                parameters.append(f'{param.name}="{param.value}"')

        parameters = " ".join(parameters)
        return (
            f"[{self._definition.group_name}:{self._definition.tag_name} {parameters}]"
        )

    @classmethod
    def from_string(cls, tag: str, config: TagConfig):
        if not (match := cls.TAG_FORMAT.match(tag)):
            raise LMS_TagInvalidFormatError(
                f"Invalid decoded tag format detected for tag '{tag}'"
            )

        is_closing = match.group(1) is not None
        group_name, tag_name = match.group(2), match.group(3)
        tag_definition = config.get_definition_by_names(group_name, tag_name)

        if is_closing:
            return cls(tag_definition, is_closing=True)

        parameters = dict(cls.PARAMETER_FORMAT.findall(tag))
        parameter_map = LMS_FieldMap.from_string_dict(
            parameters, tag_definition.parameters
        )
        return cls(tag_definition, parameter_map)


type LMS_ControlTag = LMS_EncodedTag | LMS_DecodedTag


def is_tag(obj: object) -> TypeGuard[LMS_ControlTag]:
    """Typeguard to narrow tag objects."""
    return isinstance(obj, (LMS_EncodedTag, LMS_DecodedTag))
