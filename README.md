# (X)KNX Project fork ([original](https://github.com/XKNX/xknxproject))

The purpose of this fork is to create a [Snom xml](http://docs.snom.io/xml_minibrowser/main_tags/SnomIPPhoneMenu/) for controlling a KNX installation with [Snom IP phones](https://www.snom.com/en/).  
For this, the [original xknxproject](https://github.com/XKNX/xknxproject)  was changed to obtain the groupaddresses range names (main and middle) and not only the groupaddress name.

[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=f8b424)](https://github.com/pre-commit/pre-commit)
[![Discord](https://img.shields.io/discord/338619021215924227?color=7289da&label=Discord&logo=discord&logoColor=7289da)](https://discord.gg/bkZe9m4zvw)
[![codecov](https://codecov.io/gh/XKNX/xknxproject/branch/main/graph/badge.svg?token=LgPvZpKK3k)](https://codecov.io/gh/XKNX/xknxproject)

Extracts KNX projects and parses the underlying XML.

This project aims to provide a library that can be used to extract and parse KNX project files and read out useful information including the group addresses, devices, their descriptions and possibly more.

## Documentation

Currently, xknxproject supports extracting (password protected) ETS5 and ETS6 projects and can obtain the following information:

* Areas, Lines, Devices and their individual address
* CommunicationObjectInstance references for their devices (GA assignments)
* Group Addresses and their DPT type if set
* The application programs communication objects, their respective flags and the DPT Type
* Location information of devices (in which rooms they are)

Caution: Loading a middle-sized project with this tool takes about 1.5 seconds. For bigger projects this might as well be >3s.

## Installation

1. Clone the project
2. Create a virtual environment if desired
3. Install the requirements

## Usage

```python
"""
Extract and parse a KNX project file.
Print its output as json
"""
import json

from xknxproject.models import KNXProject
from xknxproject import XKNXProj


knxproj: XKNXProj = XKNXProj("path/to/your/file.knxproj", "optional_password")
project: KNXProject = knxproj.parse()

print(json.dumps(project, indent=4))
```

The `KNXProject` is a typed dictionary and can be used just like a dictionary, or can be exported as JSON.
You can find an example file (exported JSON) in our test suite under https://github.com/XKNX/xknxproject/tree/main/test/resources/stubs

The full type definition can be found here: https://github.com/XKNX/xknxproject/blob/main/xknxproject/models/knxproject.py
