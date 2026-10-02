import hashlib
import os.path
import pathlib
from types import MappingProxyType
from typing import Literal, get_args, Mapping

import requests
import yaml

from lms.common.field.lms_datatype import LMS_DataType
from lms.flowchart.definitions.node_type import LMS_NodeType
from lms.project.msbp import MSBP
from lms.titleconfig.definitions.attribute import AttributeConfig
from lms.titleconfig.definitions.field import FieldDefinition
from lms.titleconfig.definitions.nodes import NodeConfig
from lms.titleconfig.definitions.tags import TagConfig, TagDefinition

PRESETS_URL = (
    "https://api.github.com/repos/AbdyyEee/PyLibMS/contents/lms/titleconfig/presets"
)


class TitleConfig:
    """
    Represents a configuration for a specific title.
    """

    TAG_KEY = "tag_definitions"
    ATTR_KEY = "attribute_definitions"
    NODE_KEY = "node_definitions"

    GAME_PRESET = Literal[
        "Badge Arcade",
        "Brain Age Concentration Training",
        "Kirby Planet Robobot",
        "Super Mario Odyssey",
        "Super Mario 3D Land",
        "Super Mario 3D World + Bowsers Fury",
        "The Legend of Zelda a Link Between Worlds",
        "The Legend of Zelda Echos of Wisdom",
        "Tomodachi Life Living The Dream",
        "Tomodachi Life NA-EU",
    ]

    def __init__(
            self,
            game: str | None,
            attribute_config_map: dict[str, AttributeConfig] | None = None,
            tag_config: TagConfig | None = None,
            node_config: NodeConfig | None = None,
    ):
        self._game = game
        self._attribute_config_map = attribute_config_map
        self._tag_config = tag_config
        self._node_config = node_config

    @property
    def game(self) -> str | None:
        """The name of the game for the titleconfig."""
        return self._game

    @classmethod
    def get_preset_list(cls) -> tuple[str, ...]:
        """Get the current preset list."""
        return get_args(cls.GAME_PRESET)

    @classmethod
    def check_for_preset_updates(cls) -> dict[str, bool]:
        """
        Checks whether a preset has an available update.

        :param game: the game preset.
        """
        preset_list = cls._request_preset_list()

        result = {}

        for preset in preset_list:
            if f"{preset}.yaml" not in os.listdir("presets"):
                continue

            path = os.path.join("presets", f"{preset}.yaml")

            with open(path, "rb") as f:
                data = f.read().replace(b"\r\n", b"\n")

            # Blob calculation https://git-scm.com/book/en/v2/Git-Internals-Git-Objects.html
            local_hash = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

            result[preset] = local_hash != preset_list[preset]["sha"]

        return result

    @classmethod
    def download_preset(cls, game: GAME_PRESET) -> None:
        """
        Fetches a preset from the repository and loads it to ./presets

        :param game: the game preset.

        List of presets:

        https://github.com/AbdyyEee/PylibMS/tree/main/lms/titleconfig/presets
        """

        preset_list = cls._request_preset_list()

        if game.lower() not in {
            preset.lower(): data for preset, data in preset_list.items()
        }:
            raise FileNotFoundError(f"Preset '{game}' not found.")

        raw = cls._request_preset_file(game, preset_list)

        pathlib.Path("presets").mkdir(exist_ok=True)

        path = os.path.join("presets", f"{game}.yaml")
        with open(path, "wb") as f:
            f.write(raw.content)

    @classmethod
    def _request_preset_list(cls) -> dict[str, dict]:
        result = {}

        try:
            folder_response = requests.get(PRESETS_URL, timeout=10)
            folder_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError("An error occurred fetching the preset list!") from e

        for preset in folder_response.json():
            result[os.path.basename(preset["path"]).removesuffix(".yaml")] = preset

        return result

    @classmethod
    def _request_preset_file(cls, game: str, preset_list: dict) -> requests.Response:
        try:
            raw_response = requests.get(preset_list[game]["download_url"], timeout=10)
            raw_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"An error occurred fetching the file data for preset '{game}'"
            ) from e

        return raw_response

    @property
    def tag_config(self) -> TagConfig:
        """The loaded tag config instance."""
        return self._tag_config

    @property
    def attribute_configs(self) -> Mapping[str, AttributeConfig]:
        """Returns a mapping of all attribute configurations in the configuration."""
        if self._attribute_config_map is None:
            return MappingProxyType({})
        return MappingProxyType(self._attribute_config_map)

    @property
    def node_config(self) -> NodeConfig:
        """The loaded node configuration."""
        return self._node_config

    @classmethod
    def load_file(cls, file_path: str):
        """
        Loads a config from a file.

        :param file_path: the path to the config.
        """
        with open(file_path, "r") as f:
            return TitleConfig.load_config(f.read())

    @classmethod
    def load_config(cls, content: str | dict):
        """
        Loads the config of a specified game.

        :param content: the config content, as a string or loaded as a dictionary.
        """

        if isinstance(content, str):
            parsed_content = yaml.safe_load(content)
        else:
            parsed_content = content

        game = parsed_content.get("game")

        attribute_configs = {}
        for config in parsed_content.get(cls.ATTR_KEY, []):
            config = AttributeConfig(config["name"], config.get("description", ""))
            for value_def in config["definitions"]:
                config.add_definition(FieldDefinition.from_dict(value_def))

        tag_content = parsed_content.get(cls.TAG_KEY, {})
        group_map = tag_content["groups"]
        tag_config = TagConfig(group_map)

        for tag_def in tag_content.get("tags", ()):
            tag_config.add_definition(TagDefinition.from_dict(tag_def, group_map))

        node_config = NodeConfig()

        node_data = parsed_content.get(cls.NODE_KEY, {})
        branch_data, event_data = node_data.get("branch", []), node_data.get("event", [])

        for definition in branch_data:
            node_config.add_definition(LMS_NodeType.BRANCH, definition)

        for definition in event_data:
            node_config.add_definition(LMS_NodeType.EVENT, definition)

        return cls(game, attribute_configs, tag_config, node_config)

    @staticmethod
    def generate_file(file_path: str, game: str, project: MSBP) -> None:
        """
        Generates a title config file for a specific game.

        :param file_path: the path to the YAML file.
        :param game: the name of the game to create the config for.
        :param project: a MSBP object.
        """
        with open(file_path, "w+") as f:
            yaml.safe_dump(
                TitleConfig.generate_config(game, project),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    @staticmethod
    def generate_config(game: str, project: MSBP) -> dict | None:
        """
        Generates a title config file for the specified game.

        :param game: the name of the game to create the config for.
        :param project: a MSBP object.
        """
        config = {}
        config["game"] = game

        if project.tag_groups is not None:
            config[TitleConfig.TAG_KEY] = {
                "groups": {group.group_id: group.name for group in project.tag_groups},
                "tags": [],
            }

            for group in project.tag_groups:
                for i, tag_def in enumerate(group.tag_definitions):
                    definition = {
                        "name": tag_def.name,
                        "group_id": group.group_id,
                        "tag_index": i,
                        "description": "",
                    }

                    if tag_def.parameter_definitions:
                        definition["parameters"] = []

                    for param_def in tag_def.parameter_definitions:
                        param_definition = {
                            "name": param_def.name,
                            "description": "",
                            "datatype": param_def.datatype.name.lower(),
                        }

                        if param_def.datatype is LMS_DataType.ENUM:
                            param_definition["enum_members"] = dict(param_def.enum_members)

                        definition["parameters"].append(param_definition)

                    config[TitleConfig.TAG_KEY]["tags"].append(definition)

        config[TitleConfig.ATTR_KEY] = []
        if project.attribute_definitions is not None:
            attr_definitions = []
            for attr_def in project.attribute_definitions:
                definition = {
                    "name": attr_def.name,
                    "description": "",
                    "datatype": attr_def.datatype.name.lower(),
                }
                if attr_def.datatype is LMS_DataType.ENUM:
                    definition["enum_members"] = dict(attr_def.enum_members)

                attr_definitions.append(definition)

            # Main attribute entries
            config[TitleConfig.ATTR_KEY].append(
                {
                    "name": project.name,
                    "description": "",
                    "definitions": attr_definitions,
                }
            )

        return config
