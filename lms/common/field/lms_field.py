from __future__ import annotations

from collections.abc import Iterator
from types import MappingProxyType
from typing import Mapping, TypeAlias

from lms.common.field.lms_datatype import LMS_DataType, verify_number_from_datatype
from lms.titleconfig.definitions.field import FieldDefinition

FieldValue: TypeAlias = int | str | float | bool | bytes


class LMS_FieldMap:
    """
    An immutable wrapper for a basic ``Mapping[str, LMS_Field]``.

    Fields are validated by their datatype upon modification.
    """

    def __init__(self, fields: Mapping[str, LMS_Field]) -> None:
        self._fields = MappingProxyType(fields)

    @property
    def fields(self) -> Mapping[str, LMS_Field]:
        """The fields associated to this LMS_FieldMap."""
        return self._fields

    def __len__(self) -> int:
        return len(self.fields)

    def __iter__(self) -> Iterator[LMS_Field]:
        return iter(self.fields.values())

    def __getitem__(self, name: str) -> LMS_Field:
        if name not in self.fields:
            raise KeyError(f"Field '{name}' does not exist")

        return self.fields[name]

    def __setitem__(self, name: str, value: FieldValue) -> None:
        if name not in self.fields:
            raise KeyError(f"Field '{name}' does not exist")

        self.fields[name].value = value

    def to_dict(self) -> dict[str, FieldValue]:
        """Converts the field map to a regular dictionary."""
        return {field.name: field.value for field in self.fields.values()}

    @staticmethod
    def create_default_dict_map(
            definitions: list[FieldDefinition],
    ) -> dict[str, FieldValue]:
        map = {}
        for definition in definitions:
            match definition.datatype:
                case LMS_DataType.STRING:
                    map[definition.name] = ""
                case LMS_DataType.ENUM:
                    map[definition.name] = definition.enum_members[0]
                case LMS_DataType.BOOL:
                    map[definition.name] = False
                case LMS_DataType.FLOAT32:
                    map[definition.name] = 0.0
                case _:
                    map[definition.name] = 0
        return map

    @classmethod
    def create_default_map(cls, definitions: list[FieldDefinition]):
        return cls.from_dict(LMS_FieldMap.create_default_map(definitions), definitions)

    @classmethod
    def from_dict(cls, data: dict[str, FieldValue], definitions: list[FieldDefinition]):
        return cls(
            {
                definition.name: LMS_Field(data[definition.name], definition)
                for definition in definitions
            }
        )

    @classmethod
    def from_string_dict(cls, data: dict[str, str], definitions: list[FieldDefinition]):
        fields = {}
        casted_value = None

        for definition in definitions:
            # These datatypes do not require any casting
            if definition.datatype in (LMS_DataType.STRING, LMS_DataType.ENUM):
                fields[definition.name] = LMS_Field(data[definition.name], definition)
                continue

            value = data[definition.name]
            match definition.datatype:
                case LMS_DataType.BOOL:
                    if value.lower() not in ("false", "true"):
                        raise ValueError("Invalid boolean value!")
                    casted_value = value.strip().lower() == "true"
                case LMS_DataType.FLOAT32:
                    casted_value = float(value)
                case _:
                    casted_value = int(value)

            fields[definition.name] = LMS_Field(casted_value, definition)

        return cls(fields)


class LMS_Field:
    """
    A class that represents a mapped value linked to a config definition.
    """

    def __init__(
            self,
            value: int | str | float | bytes | bool,
            definition: FieldDefinition,
    ):
        _verify_value_from_definition(value, definition)
        self._definition = definition
        self._value = value

    def __repr__(self):
        if self.datatype is LMS_DataType.LIST:
            return f"LMS_Field(value={self._value!r}, list_items={self.enum_members!r})"

        return f"LMS_Field(value={self._value!r}, type={self.datatype!r})"

    @property
    def name(self) -> str:
        """The name of the field."""
        return self._definition.name

    @property
    def description(self) -> str:
        """The description of the field."""
        return self._definition.description

    @property
    def value(self) -> int | str | float | bytes | bool:
        """The value of the field instance."""
        return self._value

    @property
    def datatype(self) -> LMS_DataType:
        """The datatype of the field instance."""
        return self._definition.datatype

    @property
    def enum_members(self) -> list[str]:
        """The list items bound to the field instance. Only is valid for ``LMS_Datatype.LIST`` values."""
        return self._definition.enum_members

    @value.setter
    def value(self, new_value: int | str | float | bytes | bool):
        _verify_value_from_definition(new_value, self._definition)
        self._value = new_value


def _verify_value_from_definition(
        value: int | str | float | bytes | bool, definition: FieldDefinition
) -> None:
    datatype = definition.datatype

    if datatype in (LMS_DataType.BOOL, LMS_DataType.STRING):
        return

    match datatype:
        case LMS_DataType.ENUM if isinstance(value, str):
            if value not in definition.enum_members.values():
                raise ValueError(
                    f"""The value of '{value}' provided for field '{definition.name}' is not a 
                    valid item in the list {definition.enum_members}."""
                )
            else:
                return
        case _ if isinstance(value, (int, float)):
            verify_number_from_datatype(value, definition.datatype)
            return

    raise TypeError(
        f"The value provided for '{definition.name}' type '{type(value)}' should be '{datatype.builtin_type}' (DATATYPE {definition.datatype})."
    )
