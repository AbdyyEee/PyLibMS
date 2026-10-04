# PyLibMS

[![Python Versions](https://img.shields.io/pypi/pyversions/PyLibMS)](https://pypi.org/project/PyLibMS/)
![LICENSE](https://img.shields.io/badge/license-MIT-blue)
[![PyPI version](https://badge.fury.io/py/PyLibMS.svg)](https://badge.fury.io/py/PyLibMS)

PyLibMS is a library built in Python 3.10 and above for reading and writing of libMessageStudio (LMS) proprietary file
formats from Nintendo.

The following is supported:

| Format | Read | Write | Support                                                                                                                                     |
|--------|------|-------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `MSBT` | ✅   | ✅    | Reading and writing Support for majority of sections. Full attribute (`ATR1`) decoding with configurations. Tag decoding 1:1 with the official Nintendo `.mstxt` file format. |
| `MSBF` | ✅   | ✅    | Reading and writing flowcharts `FLW3`. Support for custom node definitions, attaching names and descriptions to nodes. Altering parameter datatypes for flexibility between games. |
| `MSBP` | ✅   | ❌    | Viewing all MSBP relevant metadata and generating configuration files for use with `MSBT` files. |

This library is designed to support LMS revision >=3.0. These include files generated for late **Wii** titles,
**Nintendo 3DS**, **Wii U**, **Mobile**, **Nintendo Switch** and **Nintendo Switch 2** games.

# Features and Usage

Simple preview of the library is below. See [the wiki](https://github.com/AbdyyEee/PylibMS/wiki) for more explanations
and examples.

## Reading
```py
# MSBT
from lms.message.msbtio import read_msbt_path

msbt = read_msbt_path("Text.msbt")

# MSBP
from lms.project.msbpread import read_msbp_path

msbp = read_msbp_path("Project.msbp")

# MSBF
from lms.flowchart.msbfio import read_msbf_path

msbf = read_msbf_path("Flowchart.msbf")
```

## Writing
```py
# MSBT
from lms.message.msbtio import write_msbt_path

write_msbt_path("Out_text.msbt")

# MSBF
from lms.flowchart.msbfio import write_msbf_path

write_msbf_path("Out_Flowchart.msbf")
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

* [SS-Decomp](https://github.com/zeldaret/ss): Referenced some parts of their MSBF decomp when adding the format
  to [Nintendo-File-Formats](https://nintendo-formats.com) and this library.
* [Nintendo-File-Formats](https://nintendo-formats.com) by Kinnay: For existing information on the MSBT and MSBP file
  formats.
* [Trippixyz](https://github.com/Trippixyz): For helping me get started general decompilation of the formats and general
  help.
* [AeonSake](https://github.com/AeonSake): Inspiration for some the implementation of the library and a bit of general
  help.
