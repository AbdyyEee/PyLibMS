from lms.titleconfig.definitions.field import FieldDefinition


class AttributeConfig:
    """Class that represents an attribute config definition."""

    def __init__(self, name: str, description: str) -> None:
        self._name = name
        self._description = description
        self._definitions = []

    @property
    def name(self) -> str:
        """Name of the configuration."""
        return self._name

    @property
    def description(self) -> str:
        """Description of the configuration."""
        return self._description

    @property
    def definitions(self) -> tuple[FieldDefinition, ...]:
        """Definitions associated with the configuration."""
        return tuple(self._definitions)

    def add_definition(self, definition: FieldDefinition) -> None:
        self._definitions.append(definition)
