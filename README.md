# PyLibMS

[![Python Versions](https://img.shields.io/pypi/pyversions/PyLibMS)](https://pypi.org/project/PyLibMS/)
![LICENSE](https://img.shields.io/badge/license-MIT-blue)
[![PyPI version](https://badge.fury.io/py/PyLibMS.svg)](https://badge.fury.io/py/PyLibMS)
![Tests](https://github.com/abdyyeee/PyLibMS/actions/workflows/tests.yml/badge.svg?branch=main)

PyLibMS is a library built in Python 3.11 and above for reading and writing of revision >=3 of the libMessageStudio
(LMS) proprietary file formats from Nintendo. These include files generated for late **Wii** titles, **Nintendo 3DS**,
**Wii U**, **Mobile**, **Nintendo Switch** and **Nintendo Switch 2** games.

The following is supported:

| Format  | Read | Write | Support                                                                                                                                                                                      |
|---------|------|-------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `MSBT`  | ✅   | ✅    | 1:1 reading and writing. Support for majority of sections. Full attribute (`ATR1`) decoding with configurations. Tag decoding 1:1 with the official Nintendo `.mstxt` file format.           |
| `UMSBT` | ✅   | ✅    | 1:1 reading and writing. Accessing, adding, inserting and deleting `MSBT` files within `UMSBT` archives.                                                                                     |
| `MSBF`  | ✅   | ✅    | 1:1 reading and writing flowcharts (`FLW3`). Support for custom node definitions, attaching names and descriptions to nodes. Altering parameter datatypes for flexibility between games.     |
| `MSBP`  | ✅   | ✅    | 1:1 reading and writing. Support for adding/editing colors, styles, and source files. Viewable metadata for tags and attributes. Utilized as optional metadata for configuration generation. |                                                                        |

# Documentation

PyLibMS documentation is on [readthedocs](https://pylibms.readthedocs.io/en/latest/). A simple preview is below:

## Reading

```py
# MSBT
from lms.message.msbtio import read_msbt_path

msbt = read_msbt_path("Text.msbt")

# UMSBT
from lms.message.umsbtio import read_umsbt_path

umsbt = read_umsbt_path("TextU.umsbt")

# MSBP
from lms.project.msbpio import read_msbp_path

msbp = read_msbp_path("Project.msbp")

# MSBF
from lms.flowchart.msbfio import read_msbf_path

msbf = read_msbf_path("Flowchart.msbf")
```

## Writing

```py
# MSBT
from lms.message.msbtio import write_msbt_path

write_msbt_path("Out_text.msbt", msbt)

# UMSBT
from lms.message.umsbtio import write_umsbt_path

write_umsbt_path("Out_textu.umsbt")

# MSBP
from lms.project.msbpio import write_msbp_path

write_msbp_path("Project.msbp", msbp)

# MSBF
from lms.flowchart.msbfio import write_msbf_path

write_msbf_path("Out_Flowchart.msbf", msbf)
```

# Adding/Editing Presets

To add or edit Preset, you may create an issue with the relevant `yaml` file and the game it is for.

# Installation

Python version must be `>=3.11.

```
pip install PyLibMS
```

[Pip Page](https://pypi.org/project/PyLibMS/)

# Build Instructions

Clone the repository, then run `pip install`.

```bash
git clone https://github.com/AbdyyEee/PylibMS.git
cd PyLibMS
pip install -e .
```

# AI Disclaimer

PyLibMS and its code is handwritten, developed and maintained by abdyyeee.

AI was occasionally consulted for minor implementation references during the development of MSBT, USMBT and MSBF. No AI
was utilized for MSBP. Any references were reviewed and tested beforehand, and no code was ever directly pasted from any
generative source.

The development of unit-tests were AI assisted.

# Credits & Sources

* [SS-Decomp](https://github.com/zeldaret/ss): Referenced some parts of their MSBF decomp when adding the format
  to [Nintendo-File-Formats](https://nintendo-formats.com) and this library.
* [Nintendo-File-Formats](https://nintendo-formats.com) by Kinnay: For existing information on the MSBT and MSBP file
  formats.
* [Trippixyz](https://github.com/Trippixyz): For helping me get started general decompilation of the formats and general
  help.
* [AeonSake](https://github.com/AeonSake): Inspiration for UMSBT implementation and other bits of the library. 
