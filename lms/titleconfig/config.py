import hashlib
import os.path
import pathlib
from types import MappingProxyType
from typing import Literal, get_args, Mapping, Sequence, Self

import requests
import yaml

from lms.flowchart.definitions.node_type import LMS_NodeType
from lms.project.definitions.attribute import LMS_AttrDefinition
from lms.project.definitions.color import LMS_Color
from lms.project.definitions.style import LMS_Style
from lms.project.definitions.tag import LMS_TagDefinition
from lms.project.msbp import MSBP
from lms.project.msbpio import read_msbp_path
from lms.titleconfig.definitions.attribute import AttributeDefinition
from lms.titleconfig.definitions.color import Color
from lms.titleconfig.definitions.nodes import NodeConfig, NodeDefinition
from lms.titleconfig.definitions.project import Project
from lms.titleconfig.definitions.style import Style
from lms.titleconfig.definitions.tags import TagConfig, TagDefinition

PRESETS_URL = (
    "https://api.github.com/repos/AbdyyEee/PyLibMS/contents/lms/titleconfig/presets"
)

NO_COLOR = 0xFFFF

COLOR_KEY = "colors"
ATTR_KEY = "attributes"
TAG_KEY = "tags"
STYLE_KEY = "styles"
SOURCE_KEY = "source_files"
NODE_KEY = "nodes"


class TitleConfig:
    """
    Represents a configuration for a specific title.
    """

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
            nodes: Mapping[str, NodeConfig] | None = None,
            projects: Mapping[str, Project] | None = None,
    ):
        self._game = game
        self._nodes = nodes or {}
        self._projects: dict[str, Project] = projects or {}

    @property
    def game(self) -> str | None:
        """The name of the game for the titleconfig."""
        return self._game

    @property
    def node_configs(self) -> Mapping[str, NodeConfig] | None:
        """Mapping of nodes for this configuration."""
        return MappingProxyType(self._nodes)

    @property
    def projects(self) -> Mapping[str, Project]:
        """Mapping of projects located in the configuration."""
        return MappingProxyType(self._projects)

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

    @classmethod
    def load_file(cls, file_path: str) -> Self:
        """
        Loads a config from a file.

        :param file_path: the path to the config.
        """
        with open(file_path, "r") as f:
            return TitleConfig.load_config(f.read())

    @classmethod
    def load_config(cls, content: str | dict) -> Self:
        """
        Loads the config of a specified game.

        :param content: the config content, as a string or loaded as a dictionary.
        """

        if isinstance(content, str):
            parsed_content = yaml.safe_load(content)
        else:
            parsed_content = content

        game = parsed_content.get("game")
        nodes: dict = parsed_content.get("nodes", {})

        node_map = {}
        for name, definition in nodes.items():

            for node_data in [nodes.get("global", {}), definition]:
                branch_definitions = {node["id"]: NodeDefinition.from_dict(node["id"], LMS_NodeType.BRANCH, node) for
                                      node in node_data.get("branch", [])}

                event_definitions = {node["id"]: NodeDefinition.from_dict(node["id"], LMS_NodeType.EVENT, node) for
                                      node in node_data.get("event", [])}

            node_map[name] = NodeConfig(branch_definitions, event_definitions)

        projects: dict = parsed_content.get("projects", {})

        if not projects:
            return cls(game, nodes=node_map)

        project_map = {}
        global_projects = projects.get("global", {})

        for name, project in projects.items():

            project_obj = Project()
            project_obj.name = name

            for key in [COLOR_KEY, ATTR_KEY, TAG_KEY, STYLE_KEY, SOURCE_KEY]:
                current_data = project.get(key)

                # Override using global if data is omitted from the project and defined in global
                # otherwise we can continue as there is no data defined
                if current_data is None:
                    if key not in global_projects:
                        continue
                    data = global_projects[key]
                else:
                    data = current_data

                match key:
                    case "colors":
                        for color in data:
                            project_obj.add_color(Color.from_dict(color))
                    case "attributes":
                        for attribute in data:
                            project_obj.add_attribute(AttributeDefinition.from_dict(attribute))
                    case "tags":
                        groups = data["groups"]
                        container = TagConfig(groups)
                        for tag in data["definitions"]:
                            container.add_definition(TagDefinition.from_dict(tag, groups))
                        project_obj.set_tags(container)
                    case "styles":
                        for style in data:
                            project_obj.add_style(Style.from_dict(style))
                    case "source_files":
                        for source in data:
                            project_obj.add_source(source)

            project_map[name] = project_obj

        return cls(game, node_map, project_map)

    @staticmethod
    def generate_file(
            file_path: str | os.PathLike[str],
            game: str,
            project: MSBP | None = None,
    ) -> None:
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
    def generate_merged_file(
            directory: str | os.PathLike[str],
            config_path: str | os.PathLike[str],
            game: str) -> None:
        """
        Generates a config with all projects from each MSBP are merged into a file.

        :param directory: directory of MSBP files.
        :param config_path: the path to the config file.
        :param game: the name of the game to create the config for.
        """
        msbps = []

        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if not file_path.endswith(".msbp"):
                raise ValueError("Detected a non-MSBP file in the directory!")

            msbps.append(read_msbp_path(file_path))

        with open(config_path, "w+") as f:
            yaml.safe_dump(
                TitleConfig.generate_merged_config(game, msbps),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    @staticmethod
    def generate_config(game: str, msbp: MSBP | None = None) -> dict | None:
        """
        Generates a title config file for the specified game.

        :param game: the name of the game to create the config for.
        :param msbp: a MSBP object.
        """
        return {"game": game, "nodes": [], "projects": _msbp_to_dict(msbp)}

    @staticmethod
    def generate_merged_config(
            game: str,
            msbps: Sequence[MSBP]) -> dict:
        """
        Generates a config with all projects from each MSBP are merged.

        :param game: the name of the game to create the config for.
        :param msbps: a sequence of MSBP objects.
        """
        merged_projects = {}

        for msbp in msbps:
            merged_projects.update(_msbp_to_dict(msbp, False))

        return {"game": game, "projects": merged_projects}


def _msbp_to_dict(msbp: MSBP | None, global_key: bool = True) -> dict:
    if msbp is None:
        return {}

    projects = {msbp.name if not global_key else "global": {
        COLOR_KEY: (colors := []),
        ATTR_KEY: (attributes := []),
        TAG_KEY: (tags := {"groups": {}, "definitions": []}),
        STYLE_KEY: (styles := []),
        SOURCE_KEY: (source_files := []), }
    }

    for color in msbp.colors:
        colors.append(color_to_dict(color))

    for attribute in msbp.attribute_definitions:
        attributes.append(attribute_to_dict(attribute))

    for tag_group in msbp.tag_groups:
        tags["groups"][tag_group.group_id] = tag_group.name

        for i, tag in enumerate(tag_group.tag_definitions):
            tags["definitions"].append(tag_to_dict(tag_group.group_id, i, tag))

    for style in msbp.styles:
        styles.append(style_to_dict(style, msbp.colors))

    for source in msbp.source_files:
        source_files.append(source)

    return projects


def color_to_dict(color: LMS_Color) -> dict:
    return {
        "name": color.name,
        "red": color.red,
        "green": color.green,
        "blue": color.blue,
        "alpha": color.alpha,
    }


def attribute_to_dict(attribute: LMS_AttrDefinition) -> dict:
    result = {
        "name": attribute.name,
        "datatype": attribute.datatype.name.lower(),
        "offset": attribute.offset,
    }

    if attribute.enum_members:
        result["enum_members"] = dict(attribute.enum_members)

    return result


def tag_to_dict(group_id: int, tag_index: int, tag_definition: LMS_TagDefinition) -> dict:
    data = {
        "name": tag_definition.name,
        "group_id": group_id,
        "tag_index": tag_index,
    }
    if tag_definition.parameters:
        parameters = []
        for parameter in tag_definition.parameters:
            definition = {"name": parameter.name, "datatype": parameter.datatype.name.lower()}
            if parameter.enum_members:
                definition["enum_members"] = dict(parameter.enum_members)

            parameters.append(definition)
        data["parameters"] = parameters

    return data


def style_to_dict(style: LMS_Style, colors: tuple[LMS_Color]) -> dict:
    return {
        "name": style.name,
        "region_width": style.region_width,
        "line_number": style.line_number,
        "font_index": style.font_index,
        "color": None if style.color_index is None else colors[style.color_index]
    }
