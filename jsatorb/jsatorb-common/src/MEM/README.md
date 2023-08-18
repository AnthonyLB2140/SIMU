# JSatOrb project: JSatOrb common: MEM sub-module

This module generates MEM files for satellites orbiting any central body. MEM files contain a header, metadata, and data. The classes are used in `FileGenerator.py` in the ../VTS folder [(see the README)](../VTS/README.md).
The first two columns in data represent the modified Julian day date and the seconds in day. It generates one file per satellite and per data type (and per station for visibility data).

The central body can be chosen in the list provided by Orekit [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html).
The satellite coordinates in the request and in the response are expressed in the EME2000 inertial frame for Earth, and in the inertial frame associated with the central body for other central bodies as defined by Orekit (celestial body provided by `CelestialBodyFactory` class [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html) and inertial frame provided by `getInertiallyOrientedFrame` [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBody.html#getInertiallyOrientedFrame--).

For Keplerian and Cartesian satellites, the propagator is an analytical Keplerian propagator [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html).
For TLE satellites, the propagator is the Orekit propagator dedicated to TLEs [(see the class documentation here)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/propagation/analytical/tle/TLEPropagator.html).

Since TLEs specify a date, the actual initial date is the latest date between the chosen initial date and all TLE dates.

MEM files can represent:
- Keplerian Coordinates: Semi-Major Axis, Eccentricity, Inclination, RAAN, Perigee Argument, Mean Anomaly
- LLA Coordinates: Latitude, Longitude, Altitude
- Eclipse: events, either DAY or NIGHT
- Visibility: events, either START or END of visibility

For the eclipse MEM files, the dimensions of the occulting body (i.e., the central body) are described in the file `ListCelestialBodies.py`, which can be found [here](../ListCelestialBodies.py).


## Prerequisites

- Python3.7
- A specific Python environment (named JSatOrbEnv) containing the following packages (installed through the conda-forge channel):
        - Orekit 10.2 (embedding hipparchus),
        - jinja2,
        - and bottle.


## Launch the service

This service can be launched in two ways:
- directly by calling the `MEMGenerator.py` module,
- through the REST API calls when an MEM generation is needed by the API.  
In this latter case, the REST API calls the `FileGenerator.py`, which in turn calls the `MEMGenerator.py` module.  
See the [VTS sub-module documentation](../VTS/README.md) for more information.
