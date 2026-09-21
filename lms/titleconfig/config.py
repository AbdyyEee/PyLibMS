import hashlib
import os.path
import pathlib
from typing import Literal, get_args

import requests
import yaml

from lms.common.field.lms_datatype import LMS_DataType
from lms.flowchart.definitions.node_type import LMS_NodeType
from lms.project.msbp import MSBP
from lms.titleconfig.definitions.attribute import AttributeConfig
from lms.titleconfig.definitions.nodes import NodeConfig, NodeDefinition
from lms.titleconfig.definitions.tags import TagConfig, TagDefinition
from lms.titleconfig.definitions.value import ValueDefinition

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
    def download_preset(cls, game: GAME_PRESET):
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
    def tag_config(self) -> TagConfig | None:
        """The loaded tag config instance."""
        return self._tag_config

    @property
    def attribute_configs(self) -> tuple[AttributeConfig, ...]:
        """Returns a tuple of all attribute configurations in read-only form."""
        if self._attribute_config_map is None:
            return ()
        return tuple(self._attribute_config_map.values())

    def get_attribute_config(self, name: str) -> AttributeConfig:
        """
        Returns the attribute configuration given the name.

        :param name: the name of the attribute config.
        """
        if self._attribute_config_map is None:
            raise ValueError(f"There are no attribute configs!")

        if name not in self._attribute_config_map:
            raise KeyError(
                f"The attribute config '{name}' does not exist in the TitleConfig!"
            )

        return self._attribute_config_map[name]

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
        for config in parsed_content[cls.ATTR_KEY]:
            definitions = [
                ValueDefinition.from_dict(value_def)
                for value_def in config["definitions"]
            ]
            attribute_configs[config["name"]] = AttributeConfig(
                config["name"], config.get("description", ""), definitions
            )

        tag_definitions: dict[int, list[TagDefinition]] = {}
        group_map = parsed_content[cls.TAG_KEY]["groups"]

        for tag_def in parsed_content[cls.TAG_KEY]["tags"]:
            definition = TagDefinition.from_dict(tag_def, group_map)
            if definition.group_id not in tag_definitions:
                tag_definitions[definition.group_id] = []
            tag_definitions[definition.group_id].append(definition)

        tag_config = TagConfig(group_map, tag_definitions)

        branch_nodes: dict[int, NodeDefinition | tuple[NodeDefinition, ...]] = {}
        event_nodes: dict[int, tuple[NodeDefinition, ...]] = {}

        for definition in parsed_content[cls.NODE_KEY]["branch"]:
            node_id = definition["id"]

            node_definition = NodeDefinition.from_dict(
                node_id, LMS_NodeType.BRANCH, definition
            )

            if node_id not in branch_nodes:
                branch_nodes[node_id] = node_definition
                continue

            existing = branch_nodes[node_id]

            if isinstance(existing, tuple):
                branch_nodes[node_id] = existing + (node_definition,)
            else:
                branch_nodes[node_id] = (existing, node_definition)

        for definition in parsed_content[cls.NODE_KEY]["event"]:
            node_id = definition["id"]

            node_definition = NodeDefinition.from_dict(
                node_id, LMS_NodeType.EVENT, definition
            )

            if node_id not in event_nodes:
                event_nodes[node_id] = node_definition
                continue

            existing = event_nodes[node_id]

            if isinstance(existing, tuple):
                event_nodes[node_id] = existing + (node_definition,)
            else:
                event_nodes[node_id] = (existing, node_definition)

        node_config = NodeConfig(branch_nodes, event_nodes)
        return cls(game, attribute_configs, tag_config, node_config)

    @staticmethod
    def generate_file(file_path: str, game: str, project: MSBP) -> None:
        """
        Generates a title config file for a specific game.

        :param file_path: the path to the yaml file.
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
                        param_definition: dict[str, str | list] = {
                            "name": param_def.name,
                            "description": "",
                            "datatype": param_def.datatype.to_string(),
                        }

                        if param_def.datatype is LMS_DataType.LIST:
                            param_definition["list_items"] = param_def.list_items

                        definition["parameters"].append(param_definition)

                    config[TitleConfig.TAG_KEY]["tags"].append(definition)

        config[TitleConfig.ATTR_KEY] = []
        if project.attribute_definitions is not None:
            attr_definitions = []
            for attr_def in project.attribute_definitions:
                definition = {
                    "name": attr_def.name,
                    "description": "",
                    "datatype": attr_def.datatype.to_string(),
                }
                if attr_def.datatype is LMS_DataType.LIST:
                    definition["list_items"] = attr_def.list_items

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
