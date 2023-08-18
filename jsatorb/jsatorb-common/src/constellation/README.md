# JSatOrb project: Constellation sub-module

This sub-module contains Python-coded functionalities used to generate a constellation according to the Walker Delta Pattern t:p:f.
It is mainly used in the GUI for constellation generation, through the REST API.

## Prerequisites

- Python3.7
- A specific Python environment (named JSatOrbEnv) containing the following packages (installed through the conda-forge channel):
    - Orekit 10.2 (embedding hipparchus),
    - jinja2,
    - and bottle.


## Launch the service

As said above, this sub-module can only be used through the JSatOrb REST API using the following route:
`/constellationgenerator`


## How it works

This sub-module considers six arguments to generate the satellites: the radius (or semi-major axis since orbits are circular) and the inclination of all orbits, the RAAN of the first orbit (right ascension of the ascending node), and the three t:p:f parameters.

The three parameters correspond to:
- t: number of satellites
- p: number of equally spaced planes
- f: relative spacing between satellites in adjacent planes

The number of satellites per plane corresponds to t/p.
