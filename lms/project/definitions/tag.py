from __future__ import annotations

from lms.common.field.lms_datatype import LMS_DataType


class LMS_TagGroup:
    def __init__(
        self,
        name: str,
        group_id: int,
        tag_indexes: list[int],
    ):
        self._name = name
        self._id = group_id
        self._tag_indices = tag_indexes

        self.tag_definitions: list[LMS_TagDefinition] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def group_id(self) -> int:
        return self._id

    def set_all_definitions(
        self,
        tag_definitions: list["LMS_TagDefinition"],
        parameter_definitions: list["LMS_TagParamDefinition"],
        list_items: list[list[str]],
    ) -> None:

        self.tag_definitions.extend(tag_definitions[i] for i in self._tag_indices)
        for tag in self.tag_definitions:
            tag.parameter_definitions.extend(
                parameter_definitions[i] for i in tag.parameter_indices
            )
            for parameter in tag.parameter_definitions:
                if parameter.datatype is LMS_DataType.LIST:
                    parameter.list_items = [
                        list_items[i] for i in parameter.list_indices
                    ]


class LMS_TagDefinition:
    def __init__(
        self,
        name: str,
        parameter_indices: list[int],
        parameter_definitions: list[LMS_TagParamDefinition] | None = None,
    ):
        self._name = name
        self._parameter_indexes = (
            parameter_indices if parameter_indices is not None else []
        )
        self.parameter_definitions = (
            parameter_definitions if parameter_definitions is not None else []
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def parameter_indices(self) -> list[int]:
        return self._parameter_indexes


class LMS_TagParamDefinition:
    def __init__(
        self,
        name: str,
        datatype: LMS_DataType,
        list_indexes: list[int] | None = None,
    ):
        self._name = name
        self.list_items: list[str] = []

        self._datatype = datatype
        self._list_indices = list_indexes if list_indexes is not None else []

    @property
    def name(self) -> str:
        return self._name

    @property
    def datatype(self) -> LMS_DataType:
        return self._datatype

    @property
    def list_indices(self) -> list[int]:
        return self._list_indices
