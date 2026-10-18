import os
from pathlib import Path
from types import MappingProxyType
from typing import Sequence, TypeAlias, Mapping

from lms.project.definitions.style import LMS_Style
from lms.titleconfig.definitions.attribute import AttributeDefinition
from lms.titleconfig.definitions.color import Color
from lms.titleconfig.definitions.field import FieldDefinition
from lms.titleconfig.definitions.style import Style
from lms.titleconfig.definitions.tags import TagConfig

# Typealias for virtual CTI1 paths
MessageSource: TypeAlias = str

class Project:
    """
    Class that represents a project entry in a configuration.
    """
    def __init__(self, name: str = "") -> None:
        self._name = name
        self._colors: list[Color] = []
        self._attributes: list[AttributeDefinition] = []
        self._tags: TagConfig = TagConfig()
        self._styles: list[Style] = []
        self._sources: list[MessageSource] = []

    @property
    def name(self) -> str:
        """The name of the project."""
        return self._name

    @property
    def colors(self) -> tuple[Color, ...]:
        """Colors associated with the project."""
        return tuple(self._colors)

    @property
    def attributes(self) -> tuple[AttributeDefinition, ...]:
        """Attributes associated with the project."""
        return tuple(self._attributes)

    @property
    def tags(self) -> TagConfig:
        """Tags associated with the project."""
        return self._tags

    @property
    def styles(self) -> tuple[Style, ...]:
        """Styles associated with the project."""
        return tuple(self._styles)

    @property
    def sources(self) -> tuple[MessageSource, ...]:
        """Source files associated with the project."""
        return tuple(self._sources)

    def add_color(self, color: Color) -> None:
        """Adds a color to the project."""
        self._colors.append(color)

    def add_attribute(self, attribute: FieldDefinition) -> None:
        """Adds a field definition to the project."""
        self._attributes.append(attribute)

    def set_tags(self, container: TagConfig) -> None:
        """Sets the tags associated with the project."""
        self._tags = container

    def add_style(self, style: Style) -> None:
        """Adds a style to the project."""
        self._styles.append(style)

    def add_source(self, source: MessageSource) -> None:
        """Adds a source to the project."""
        self._sources.append(source)



