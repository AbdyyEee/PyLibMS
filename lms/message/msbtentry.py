from lms.common.field.lms_field import LMS_FieldMap
from lms.message.lms_messagetext import LMS_MessageText
from lms.project.definitions.style import LMS_Style
from lms.titleconfig.definitions.project import Project
from lms.titleconfig.definitions.style import Style
from lms.titleconfig.definitions.tags import TagConfig


class MSBTEntry:
    """A class that represents an entry in a MSBT file."""

    def __init__(
            self,
            name: str,
            *,
            message: LMS_MessageText | str | None = "",
            attribute: LMS_FieldMap | bytes | None = None,
            style_index: int | None = None,
            project: Project | None = None,
    ):
        self.name = name

        if not isinstance(message, (LMS_MessageText, str)):
            raise TypeError(
                f"An invalid type was provided for text in entry '{name}'! Expected LMS_MessageText object or str got {type(message)}"
            )

        if isinstance(message, str):
            self._message = LMS_MessageText(message)
        else:
            self._message = message

        if attribute is not None and not isinstance(attribute, (LMS_FieldMap, bytes)):
            raise TypeError(
                f"An invalid type was provided for attribute in entry '{name}'. "
                f"Expected LMS_FieldMap or bytes, got {type(attribute)}"
            )

        self._attribute = attribute
        self.style_index = style_index
        self._project = project

    @property
    def message(self) -> LMS_MessageText:
        """The message object for the instance."""
        return self._message

    @property
    def attribute(self) -> LMS_FieldMap | bytes | None:
        """The attribute for the instance."""
        return self._attribute

    @property
    def style(self) -> Style:
        """Style object for the instance, set from a project."""
        if self._project is None:
            raise ValueError("A project must be provided for MSBT entry to view styles!")

        if self._project.styles is None or self.style_index is None:
            raise ValueError(f"There are no style definitions in the project '{self._project.name}'!")

        return self._project.styles[self.style_index]

    def set_style(self, new: Style) -> None:
        """
        Sets the style of the MSBT entry given a style object.

        :param new: the new style object to set.
        """
        if self._project is None:
            raise ValueError("A project must be provided for MSBT entry to set styles!")

        if self._project.styles is None:
            raise ValueError(f"There are no style definitions in the project '{self._project.name}'!")

        style_index = None
        for i, style in enumerate(self._project.styles):
            if style.name == new.name:
                style_index = i
                break

        if style_index is None:
            raise ValueError(f"The style '{new.name}' does not exist in the project '{self._project.name}'!")

        self.style_index = style_index

    def to_dict(self) -> dict:
        """Converts the MSBTEntry instance into a dictionary object."""
        result: dict[str, int | str | dict | None] = {
            "name": self.name,
            "message": "" if self.message is None else self.message.text,
        }

        if self._attribute is not None:
            if isinstance(self._attribute, bytes):
                result["attribute"] = self._attribute.hex().upper()
            else:
                result["attribute"] = self._attribute.to_dict()

        result["style_index"] = self.style_index
        return result

    @classmethod
    def from_dict(
            cls,
            data: dict,
            attribute_config: AttributeConfig | None = None,
            tag_config: TagConfig | None = None,
    ):
        """
        Creates a MSBTEntry from a dictionary object.

        :param data: the dictionary data.
        :param attribute_config: the config to use to import decoded attributes.
        :param tag_config: the config to use if decoded tags are included in the message.
        """
        message = data.get("message", "")
        attribute = data.get("attribute")
        style_index = data.get("style_index")

        if tag_config is not None:
            message = LMS_MessageText(message, tag_config)

        if attribute is not None:
            if not isinstance(attribute, (dict, str)):
                raise TypeError("Invalid attribute type provided!")

            if isinstance(attribute, dict):
                if attribute_config is None:
                    raise TypeError(
                        "A valid attribute config must be provided for decoded attributes!"
                    )
                attribute = LMS_FieldMap.from_dict(
                    attribute, attribute_config.definitions
                )
            else:
                attribute = bytes.fromhex(attribute)

        return cls(
            data["name"], message=message, attribute=attribute, style_index=style_index
        )
