# JSatOrb Project: Eclipse Calculator 

This module computes eclipse calculation for the Earth (WGS84) and the Sun.


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
By default the service is running on the **port 8000**.


# Run the tests

To run the tests, use the following command:  
```python test/Test[TEST_NAME].py``` where [TEST_NAME] is the name of the test to run or  
if you already ran the global tests script (`runAllTests.sh`) from the `jsatorb` module, you should have a `runTests.sh` script available in this module folder.

In this case, you can run it directly:  
```./runTests.sh```
This script will run all tests available in the test folder (all files satisfying the test/Test*.py pattern).


## Eclipse Request Example

This request to the REST API contains a demand to the backend to process an Eclipse calculation of the Sun by the Earth, from a given satellite from the 1st to the 2nd of December 2011.  

Route : '/propagation/eclipses', POST method
```json
{
  "header": {
    "timeStart": "2011-12-01T16:43:45",
    "timeEnd": "2011-12-02T16:43:45"
  },
  "satellite": {
      "type": "keplerian",
      "sma": "7128137.0",
      "ecc": "0.007014455530245822",
      "inc": "98.55",
      "pa": "90.0",
      "raan": "5.191699999999999",
      "meanAnomaly": "359.93"
  }
}
```


## Eclipse Response Example

The response is an array of sunlight time intervals.

Example of response:

```json
[
  {
    "start": "2011-12-01T16:43:45.000",
    "end": "2011-12-01T17:01:36.742"
  },
  {
    "start": "2011-12-01T18:09:02.781",
    "end": "2011-12-01T18:41:25.530"
  },
  [...]
]
```

Some other examples can be found [in the files here](./test-rest/eclipseCalculator-request.http).

## Module's sequence diagram

```plantuml
@startuml
    skinparam backgroundColor #EEEBDC
    skinparam handwritten false
    actor Student
    Student -> "REST API" : JSON request
    activate "REST API"
    "REST API" -> "BACKEND EclipseCalculator.py" : mission data set
    "BACKEND EclipseCalculator.py" -> Orekit : orbit and handler
    Orekit -> "BACKEND EclipseCalculator.py" : propagated orbit and eclipse dates
    "BACKEND EclipseCalculator.py" -> "REST API" : eclipse dates
    deactivate "REST API"    
@enduml
```

 _Remarks:_
- JSatOrb client can be the Web GUI or a batch client.
- The REST API is the centralized REST API which code is in the jsatorb-rest-apî/JSatOrbREST.py Python module.
- The back-end code is in the jsatorb-eclipse-service/src/EclipseCalculator.py Python module.
