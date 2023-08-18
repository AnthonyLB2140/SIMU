# JSatOrb project : JSatOrb Common libraries

The JSatOrb Common module is not strictly speaking an independent service as other modules. Therefore, there is no "Launch the service " section in this present documentation.
It however exists to gather common tools and libraries useful to the JSatOrb software into sub-modules described below.


# Module content

The JSatOrb Common folder contains different sub-modules that serve various purposes. For more information about these sub-modules, please read the README.md in each [SUB-MODULE]/src sub-folder.

The features provided by the current sub-modules are:

- __AEM:__ AEM attitude file generator,
- __constellation:__ Constellation generator,
- __file-conversion:__ Conversion from CCSDS files to CIC ones, readable by VTS,
- __MEM:__ MEM file generator (MEM files can be eclipse, Keplerian or LLA coordinates, or visibility from station),
- __mission-mgmt:__ User mission data management,
- __VTS:__ Global file generator for VTS (calls OEM, AEM and MEM generators) and VTS file generator.


## Prerequisites for the tests

In addition to the other prerequisites that can be found in each sub-module's README.md, Numpy and dependencies have to be installed before running the tests.
It works with Numpy 1.18.1, available on conda (`conda install numpy=1.18.1`).


# Run the tests

To run the tests, use the following command:  
```python test/Test[TEST_NAME].py``` where [TEST_NAME] is the name of the test to run or  
if you already ran the global tests script (`runAllTests.sh`) from the `jsatorb` module, you should have a `runTests.sh` script available in this module folder.

In this case, you can run it directly:  
```./runTests.sh```
This script will run all tests available in the test folder (all files satisfying the test/Test*.py pattern).
