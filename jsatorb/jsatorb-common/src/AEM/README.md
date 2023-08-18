# JSatOrb project: JSatOrb common: AEM sub-module

This module generates AEM attitude files for satellites orbiting any central body. AEM files contain a header, metadata, and data. The classes are used in `FileGenerator.py` in the ../VTS folder [(see the README)](../VTS/README.md). The attitude is given in quaternions, and the location of the scalar portion of the quaternion is indicated in the metadata (either `'FIRST'` or `'LAST'`). It generates one file per satellite.

The central body can be chosen in the list provided by Orekit [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html).
The satellite coordinates in the request and the attitude quaternions in the response are expressed in the EME2000 inertial frame for Earth, and in the inertial frame associated with the central body for other central bodies as defined by Orekit (celestial body provided by `CelestialBodyFactory` class [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html) and inertial frame provided by `getInertiallyOrientedFrame` [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBody.html#getInertiallyOrientedFrame--).

For Keplerian and Cartesian satellites, the propagator is an analytical Keplerian propagator [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html).
For TLE satellites, the propagator is the Orekit propagator dedicated to TLEs [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/propagation/analytical/tle/TLEPropagator.html).

Since TLEs specify a date, the actual initial date is the latest date between the chosen initial date and all TLE dates.


## List of attitudes

- Body center Pointing:
    - "POINTING_CENTRAL": Z-axis pointing towards central body
- LOF (Local Orbital Frame)
    - "LOF_LVLH": Constant for Local Vertical, Local Horizontal frame (X-axis aligned with position, Z-axis aligned with orbital momentum).
    - "LOF_QSW": Constant for QSW frame (X-axis aligned with position, Z-axis aligned with orbital momentum).
    - "LOF_TNW": Constant for TNW frame (X-axis aligned with velocity, Z-axis aligned with orbital momentum).
    - "LOF_VNC": Constant for Velocity - Normal - Co-normal frame (X-axis aligned with velocity, Y-axis aligned with orbital momentum).
    - "LOF_VVLH": Constant for Vehicle Velocity, Local Horizontal frame (Z-axis aligned with opposite of position, Y-axis aligned with opposite of orbital momentum).
- Nadir Pointing:
    - "NADIR": Z-axis pointing towards the vertical of the ground point under satellite
- Sun Pointing:
    - "POINTING_SUN": Z-axis pointing towards Sun


## Prerequisites

- Python3.7
- A specific Python environment (named JSatOrbEnv) containing the following packages (installed through the conda-forge channel):
        - Orekit 10.2 (embedding hipparchus),
        - jinja2,
        - and bottle.


## Launch the service

This service can be launched in two ways:
- directly by calling the `AEMGenerator.py` module,
- through the REST API calls when an AEM generation is needed by the API.  
In this latter case, the REST API calls the `FileGenerator.py`, which in turn calls the `AEMGenerator.py` module.  
See the [VTS sub-module documentation](../VTS/README.md) for more information.
