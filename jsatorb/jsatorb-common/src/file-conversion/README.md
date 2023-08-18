# JSatOrb project: File Conversion sub-module

This sub-module contains Python-coded functionalities used to convert files from the widely-used CCSDS format to the CIC CCSDS format used in VTS.
It is mainly used by the VTS sub-module (in FileGenerator.py) to convert OEM and AEM files generated in CCSDS format by Orekit. MEME files are directly generated in the CIC format and therefore do not need this conversion.


## Prerequisites

- Python3.7
- A specific Python environment (named JSatOrbEnv) containing the following packages (installed through the conda-forge channel):
    - Orekit 10.2 (embedding hipparchus),
    - jinja2,
    - and bottle.


## Launch the service

As said above, this sub-module is used by FileGenerator.py in the VTS sub-module.


## How it works

This sub-module deals with the conversion of CCSDS files into CIC CCSDS files, for the OEM (position and velocity) and AEM (attitude) files. For satellites orbiting Earth, the conversion mainly consists of a conversion of the ISO dates into Modified Julian Day dates, and a conversion from meters to kilometers.

For satellites not orbiting Earth, VTS needs position, velocity, and attitude in the EME2000 frame, whereas Orekit uses the inertial frame associated with the body. Therefore, in addition to the previous conversions (in common for Earth-orbiting satellites), the file conversion sub-module provides a rotation between the inertial frame of the body used in Orekit and the EME2000 axes.
