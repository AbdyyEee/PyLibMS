# PyLibMS

PylibMS is a library built in Python 3.12+ for the libMessageStudio (LMS) proprietary file formats (`msbt`, `msbp`,
`msbf`) from Nintendo. It supports the following:

| Format | Read | Write | Configuration Support                                                                     |
|-------------|------|-------|-------------------------------------------------------------------------------------------|
| MSBT        | ✅    | ✅     | Complete attribute decoding + tag decoding down to official `mstxt` Nintendo tool syntax. |
| MSBF        | ✅    | ✅     | Flexible node + parameter decoding through configuration definitions.                     |
| MSBP        | ✅    | ❌     | N/A                                                                                       |

This library is designed to support LMS revision 3.0+ from most Nintendo consoles. 

**Note**: MSBF files that use `FLW1` and `FLW2` are not supported, and will not be supported as they are revision <3.0 of LMS.

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
pip install PylibMS
```

[Pip Page](https://pypi.org/project/PyLibMS/)

# Build Instructions

Python version must be `>=3.12.`

Clone the repository, then run `pip install` (venv recommended)

```bash
git clone https://github.com/AbdyyEee/PylibMS.git
cd PylibMS
pip install -e 
```

# Credits & Sources

* [Nintendo-File-Formats](https://nintendo-formats.com) by Kinnay: For existing information on the MSBT and MSBP file
  formats.
* [Trippixyz](https://github.com/Trippixyz): For helping me get started general decompilation of the formats and general
  help.
* [AeonSake](https://github.com/AeonSake): Inspiration for some the implementation of the library and a bit of general
  help.
