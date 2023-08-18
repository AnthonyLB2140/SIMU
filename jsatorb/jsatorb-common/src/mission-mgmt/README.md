# JSatOrb project: Mission management sub-module

This sub-module contains Python-coded functionalities used to enable the JSatOrb client (the official GUI or any other JSatOrb client) to store mission data sets. Access to those functionalities is done through the REST API.


## Prerequisites

- Python3.7
- A specific Python environment (named JSatOrbEnv) containing the following packages (installed through the conda-forge channel):
    - Orekit 10.2 (embedding hipparchus),
    - jinja2,
    - and bottle.


## Launch the service

This service can be launched in two ways:
- directly by calling the `MissionDataManager.py` Python module,
- through the REST API calls when manipulating the JSatOrb mission data sets is needed by the API. 


## How it works

The mission data management sub-module offers functions to load, store, list or delete mission data sets.  
Those mission data sets are used to store all parameters needed by a JSatOrb simulation to be processed by the JSatOrb backend and can then be visualized with the VTS visualization tool.

Each mission data set is stored as a single *.jso file in the User's home directory (in a **~/JSatOrb/mission-data** sub-folder).
The source code is self-documented and therefore, can be used to understand precisely how this sub-module works.  

If you are looking for detailed REST working information, look into the **JSatorbREST.py** Python module of the **jsatorb-rest-api** module.


## How-to-use this module

If you are looking for requests examples to use those functionalities, look into the **test-rest/MissionDataManager.http** file of the **jsatorb-rest-api** module.
