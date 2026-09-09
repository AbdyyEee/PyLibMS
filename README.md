# PyLibMS
[![Python Versions](https://img.shields.io/pypi/pyversions/PyLibMS)](https://pypi.org/project/PyLibMS/) 
[![PyPI version](https://badge.fury.io/py/PyLibMS.svg)](https://badge.fury.io/py/PyLibMS)

PyLibMS is a library built for Python 3.10 and above for the libMessageStudio (LMS) proprietary file formats from Nintendo. 

The following is supported
| Format | Read | Write | Configuration Support                                                                     |
|-------------|------|-------|-------------------------------------------------------------------------------------------|
| `MSBT`        | ✅    | ✅     | Support for full attribute (`ATR1`) decoding. Tag decoding 1:1 with the official Nintendo `.mstxt` file format. |
| `MSBF`        | ✅    | ✅     | Support for custom node definitions, attaching names and descriptions to nodes. Altering parameter datatypes for flexibility between games.  |
| `MSBP`        | ✅    | ❌     | N/A                                                                                       |

This library is designed to support LMS revision >=3.0. These include files generated for late **Wii** titles, **Nintendo 3DS**, **Wii U**, **Mobile**, **Nintendo Switch** and **Nintendo Switch 2** games.

# Features and Usage

Simple preview of the library is below. See [the wiki](https://github.com/AbdyyEee/PylibMS/wiki) for more explanations
and examples.

## Reading

MSBT/MSBF

```py
from lms.message.msbtio import read_msbt_path
from lms.flowchart.msbfio import read_msbf_path

msbt = read_msbt_path("Game.msbt")
msbf = read_msbf_path("Game_Flowchart.msbf")
```

## Writing

```py
from lms.message.msbtio import write_msbt_path
from lms.flowchart.msbfio import write_msbf_path

write_msbt_path("Out_Game.msbt")
write_msbf_path("Out_Game_Flowchart.msbt")
```

# Adding/Editing Presets

To add or edit Preset, you may create an issue with the relevant `yaml` file and the game it is for.

# Installation

```
pip install PyLibMS
```

[Pip Page](https://pypi.org/project/PyLibMS/)

# Build Instructions

Python version must be `3.10` or higher.

Clone the repository, then run `pip install` (venv recommended)

```bash
git clone https://github.com/AbdyyEee/PylibMS.git
cd PyLibMS
pip install -e .
```

# Credits & Sources

* [Nintendo-File-Formats](https://nintendo-formats.com) by Kinnay: For existing information on the MSBT and MSBP file
  formats.
* [Trippixyz](https://github.com/Trippixyz): For helping me get started general decompilation of the formats and general
  help.
* [AeonSake](https://github.com/AeonSake): Inspiration for some the implementation of the library and a bit of general
  help.
