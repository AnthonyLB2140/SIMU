# JSatOrb project: Mission Analysis

This module uses Orekit to process satellites propagation and visibility calculations related to ground stations.  
It is mainly used for the generation of OEM files through the FileGenerator class in the ../jsatorb-common/VTS folder. [The corresponding documentation is here](../jsatorb-common/VTS/README.md).  

The central body can be chosen in the list provided by Orekit [(see this document)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html).  

The satellite coordinates in the request and in the response are expressed in the EME2000 inertial frame for Earth, and in the inertial frame associated with the central body for other central bodies as defined by Orekit (celestial body provided by `CelestialBodyFactory` class [(see this document)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html) and inertial frame provided by `getInertiallyOrientedFrame` [(see this document)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBody.html#getInertiallyOrientedFrame--).  

For Keplerian and Cartesian satellites, the propagator is an analytical Keplerian propagator [(see this document)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/bodies/CelestialBodyFactory.html).  
For TLE satellites, the propagator is the Orekit propagator dedicated to TLEs [(see this document)](https://www.orekit.org/site-orekit-10.1/apidocs/org/orekit/propagation/analytical/tle/TLEPropagator.html).  

Since TLEs specify a date, the actual initial date is the latest date between the chosen initial date and all TLE dates.


## Prerequisites

- Python3.7
- A specific Python environment (named JSatOrbEnv) containing the following packages (installed through the conda-forge channel):
    - Orekit 10.2 (embedding hipparchus),
    - jinja2,
    - and bottle.


## Launch the service

This module is accessible through the JSatOrb centralized REST API which can be launched using the following commands:

Go into the REST API folder
```
cd jsatorb-rest-api
```
Activate the conda/python environment
```
conda activate JSatOrbEnv
```
Run the REST API
```
python src/JSatOrbREST.py
```
By default the service is running on **port 8000**.


## Request and Response Examples

Examples of OEM file generation (main purpose of this code) can be found in [the document here](../jsatorb-common/test-rest/fileGenerator-request.http), through the `FileGenerator.py` class.  
It can also be used to compute visibilities, even though they can also be computed in the ../jsatorb-common/MEM folder.


### Visibility Request Example

Route : /propagation/visibility', POST method
```json
{
  "header": {
    "timeStart": "2011-12-01T16:43:45",
    "timeEnd": "2011-12-02T16:43:45",
    "step": "60"
  },
  "satellites": [
    {"name": "Sat",
    "type": "keplerian",
    "sma": 6801682.16,
    "ecc": 0.0012566,
    "inc": 52.03041,
    "pa": 128.74852,
    "raan": 72.67830,
    "meanAnomaly": 67.79703
    }
  ],
  "groundStations": [
      {"name": "TLS",
      "latitude": "43.5",
      "longitude": "1.5",
      "altitude": "100",
      "elevation": "5.0"
      }
  ]
}
```

### Visibility Response Example

Route : /propagation/visibility', POST method
```json
{
  "TLS": {
    "Sat": [
      {
        "startDate": "2011-12-02T01:20:45.000",
        "startAz": 162.47910115367816,
        "passing": false,
        "endDate": "2011-12-02T01:25:45.000",
        "endAz": 91.12912056255888
      },
      {
        "startDate": "2011-12-02T02:55:45.000",
        "startAz": 227.86239040514803,
        "passing": false,
        "endDate": "2011-12-02T03:03:45.000",
        "endAz": 59.41780052967108
      },
      [...]
    ]
  }
}
```

Other examples of requests can be found [in the visibility REST test file](../jsatorb-rest-api/test-rest/visibility-request.http).


## Module's sequence diagram

```plantuml
@startuml
    skinparam backgroundColor #EEEBDC
    skinparam handwritten false
    actor Student
    Student -> "REST API" : JSON request
    activate "REST API"
    "REST API" -> "BACKEND MissionAnalysis.py" : mission data set
    "BACKEND MissionAnalysis.py" -> Orekit : orbit
    Orekit -> "BACKEND MissionAnalysis.py" : propagated orbit
    "BACKEND MissionAnalysis.py" -> "OEMAndJSONConverter.py" : positions, velocities, and/or visibility dates
    "OEMAndJSONConverter.py" -> "BACKEND MissionAnalysis.py" : ephemerides/visibility dates in specified format
    "BACKEND MissionAnalysis.py" -> "REST API" : returning ephemerides/visibility dates
    deactivate "REST API"    
@enduml
```
 
_Remarks:_
- JSatOrb client can be the Web GUI or a batch client.
- The REST API is the centralized REST API which code is in the jsatorb-rest-apî/JSatOrbREST.py Python module.
- The back-end code is in the jsatorb-visibility-service/src Python folder.