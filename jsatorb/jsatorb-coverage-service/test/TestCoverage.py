import orekit
vm = orekit.initVM()

import traceback
import unittest
import sys
import os
import numpy as np

from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.hipparchus.geometry.spherical.twod import S2Point, SphericalPolygonsSet
from org.hipparchus.ode.events import Action
from org.hipparchus.util import FastMath

from org.orekit.bodies import OneAxisEllipsoid, CelestialBodyFactory, GeodeticPoint
from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.analytical import KeplerianPropagator
from org.orekit.propagation.events import EclipseDetector, ElevationDetector, EventsLogger, GeographicZoneDetector
from org.orekit.propagation.events.handlers import ContinueOnEvent, EventHandler, PythonEventHandler
from org.orekit.propagation.sampling import OrekitFixedStepHandler, PythonOrekitFixedStepHandler
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.time import DateTimeComponents, DateComponents, TimeComponents
from org.orekit.utils import IERSConventions, PVCoordinates

sys.path.append('src')
sys.path.append('../jsatorb-common/src')
sys.path.append('../jsatorb-common/src/VTS')
sys.path.append('../jsatorb-common/src/MEM')
sys.path.append('../jsatorb-common/src/AEM')
sys.path.append('../jsatorb-common/src/file-conversion')
sys.path.append('../jsatorb-visibility-service/src')

from ListCelestialBodies import ListCelestialBodies
from CoverageGenerator import CoverageGenerator
from FileGenerator import FileGenerator

class TestCoverage(unittest.TestCase):
    """
    This class tests the calculation of coverage, using Orekit's elevation detector 
    near the Equator and near the North pole.
    """

    @classmethod
    def setUpClass(cls):
        """
        Compute coverage for two satellites, one defined with Keplerian coordinates
        and another one with cartesian coordinates, around Earth
        """

        header = {
            "mission": "validation",
            "celestialBody": "EARTH",
            "timeStart": "2011-12-01T16:43:45",
            "timeEnd": "2011-12-02T16:43:45",
            "step": "10"
        }

        cls.satellites = [
            {"name": "KepSat",
            "type": "keplerian",
            "sma": 7000000,
            "ecc": 0.007014455530245822,
            "inc": 51,
            "pa": 20,
            "raan": 15,
            "meanAnomaly": 10
            },
            {"name": "CartSat",
            "type": "cartesian",
            "x": -6142438.668,
            "y": 3492467.560,
            "z": -25767.25680,
            "vx": 505.8479685,
            "vy": 942.7809215,
            "vz": 7435.922231
            }
        ]

        cls.optionsCoverage = {
            "timeStart": "2011-12-01T00:00:00",
            "timeEnd": "2011-12-01T08:00:00",
            "step": 60,
            "elevation": 0,
            "nbSatsToCover": 1,
            "regionLatitudes": [-40, 60],
            "regionLongitudes": [-130, 90],
            "plotType": "PERCENT_COV"
        }

        cls.celestialBody = header["celestialBody"]

        celestialBody = CelestialBodyFactory.getBody(cls.celestialBody)
        if cls.celestialBody == 'EARTH':
            bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
            cls.inertialFrame = FramesFactory.getEME2000()
        else:
            bodyFrame = celestialBody.getBodyOrientedFrame()
            cls.inertialFrame = celestialBody.getInertiallyOrientedFrame()

        celestialBodyShape = ListCelestialBodies.getBody(cls.celestialBody)
        radiusBody = celestialBodyShape.radius
        flatBody = celestialBodyShape.flattening
        cls.body = OneAxisEllipsoid(radiusBody, flatBody, bodyFrame)
        cls.mu = celestialBody.getGM()
                
        cls.utc = TimeScalesFactory.getUTC()
        cls.covGen = CoverageGenerator(cls.celestialBody, cls.satellites)
        cls.covGen.compute(cls.optionsCoverage)
        
    
    def testNbSatsToCover(self):
        """
        Tests if the number of satellites needed for coverage
        is rightly considered
        """

        dataOneSatToCover = self.covGen.getTypeData()

        optionsCoverageTwoSatsToCover = dict(self.optionsCoverage)
        optionsCoverageTwoSatsToCover["nbSatsToCover"] = 2

        covGenTwoSatsToCover = CoverageGenerator(self.celestialBody, self.satellites)
        covGenTwoSatsToCover.compute(optionsCoverageTwoSatsToCover)
        dataTwoSatsToCover = covGenTwoSatsToCover.getTypeData()

        self.assertTrue(np.all(dataOneSatToCover >= dataTwoSatsToCover))
        self.assertFalse(np.all(dataOneSatToCover == dataTwoSatsToCover))

    def testRegion(self):
        """
        Tests if the specified region to consider is taken into account
        """

        dataSetUp = self.covGen.getTypeData()

        optionsCoverageRegion = dict(self.optionsCoverage)
        optionsCoverageRegion["regionLatitudes"] = [-39.5, -34]
        optionsCoverageRegion["regionLongitudes"] = [-105.5, 35.5]
        covGenRegion = CoverageGenerator(self.celestialBody, self.satellites)
        covGenRegion.compute(optionsCoverageRegion)
        dataRegion = covGenRegion.getTypeData()

        self.assertTrue(np.shape(dataSetUp) == (100, 220))
        self.assertTrue(np.shape(dataRegion) == (6, 142))
    
    def testValuesEquator(self):
        """
        Tests if four stations located at the four vertices of a unit region
        located near the Equator would have the same combined visibility (satellite
        visible from at least one station) as the one computed with
        CoverageAnalysis.py.
        """

        sats = [
            {"name": "KepSat",
            "type": "keplerian",
            "sma": 7000000,
            "ecc": 0.007014455530245822,
            "inc": 51,
            "pa": 20,
            "raan": 15,
            "meanAnomaly": 10
            },
        ]

        optionsCov = {
            "timeStart": "2011-12-01T00:00:00",
            "timeEnd": "2011-12-02T00:00:00",
            "step": 1.,
            "elevation": 0,
            "nbSatsToCover": 1,
            "regionLatitudes": [-1, 0],
            "regionLongitudes": [0, 1],
            "plotType": "PERCENT_COV"
        }
    
        covGenTestValues = CoverageGenerator(self.celestialBody, sats)
        covGenTestValues.compute(optionsCov)
        percentCovTest = covGenTestValues.getTypeData()
        
        # Test using Keplerian coords file and visibility
        options = {"KEPLERIAN":{}}
        fileGenerator = FileGenerator(optionsCov["timeStart"], optionsCov["timeEnd"],
            optionsCov["step"], self.celestialBody, sats, [], options)

        dataFolder = 'test/files/'
        if not os.path.isdir(dataFolder):
            os.mkdir(dataFolder)
        fileGenerator.generate(dataFolder)
        
        satFileKep = dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        satKep = np.genfromtxt(satFileKep, skip_header=15)

        # Definition of four vertices
        listLatitudes = [-1., -1., 0., 0.]
        listLongitudes = [0., 1., 0., 1.]
        listElevationDetector = []
        for i in range(4):
            latStation = FastMath.toRadians(listLatitudes[i])
            longStation = FastMath.toRadians(listLongitudes[i])
            altStation = 0.
            elevStation = FastMath.toRadians(float(optionsCov["elevation"]))

            station = GeodeticPoint(latStation, longStation, altStation)
            frameStation = TopocentricFrame(self.body, station, 'myStation')
            elevationDetector = ElevationDetector(frameStation)
            elevationDetector = elevationDetector.withConstantElevation(elevStation)
            listElevationDetector.append(elevationDetector)

        # Compute times
        mjd = np.trunc(satKep[:,0])
        seconds = satKep[:,1]
        initialDate = AbsoluteDate(optionsCov["timeStart"], self.utc)
        endDate = AbsoluteDate(optionsCov["timeEnd"], self.utc)

        listDates = []
        listStates = []
        valueVisOld = [0, 0, 0, 0]
        listIDStations = []

        for i in range(len(mjd)):
            # get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)

            # Find 0 of Elevation Detector function to get events
            sma = float(satKep[i,2])*1e3
            ecc = float(satKep[i,3])
            inc = FastMath.toRadians(float(satKep[i,4]))
            raan = FastMath.toRadians(float(satKep[i,5]))
            pa = FastMath.toRadians(float(satKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(satKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)

            for i in range(4):
                valueVis = listElevationDetector[i].g(
                    SpacecraftState(currentOrbit))

                if valueVisOld[i] < 0 and valueVis > 0:
                    listDates.append(absoluteDate)
                    listStates.append('START')
                    listIDStations.append(i)
                elif valueVisOld[i] > 0 and valueVis < 0:
                    listDates.append(absoluteDate)
                    listStates.append('END')
                    listIDStations.append(i)

                valueVisOld[i] = valueVis

        # Extract combined visibility of the four stations from visibility
        # of each station
        listStarted = []
        totalListDates = []
        totalListStates = []
        for i, date in enumerate(listDates):
            state = listStates[i]
            idStation = listIDStations[i]
            if len(listStarted) == 0:
                if state == 'END':
                    if len(totalListDates) != 0:
                        totalListDates = []
                        totalListStates = []
                    totalListDates.append(initialDate)
                    totalListStates.append('START')
                    totalListDates.append(date)
                    totalListStates.append('END')
                elif state == 'START':
                    totalListDates.append(date)
                    totalListStates.append('START')
                    listStarted.append(idStation)
            elif idStation not in listStarted:
                listStarted.append(idStation)
            elif len(listStarted) == 1 and idStation in listStarted:
                totalListDates.append(date)
                totalListStates.append('END')
                listStarted.remove(idStation)
            elif idStation in listStarted:
                listStarted.remove(idStation)
            else:
                raise ValueError

        # Percent coverage
        totalDuration = endDate.durationFrom(initialDate)
        visibilityDuration = 0.
        for i, event in enumerate(totalListStates):
            date = totalListDates[i]
            if event == 'START':
                initEvent = date
                if i == len(totalListStates)-1:
                    endEvent = endDate
                    visibilityDuration += endEvent.durationFrom(initEvent)
            else:
                endEvent = date
                if i == 0:
                    initEvent = initialDate
                visibilityDuration += endEvent.durationFrom(initEvent)

        visibilityPercent = visibilityDuration/totalDuration
        self.assertAlmostEqual(percentCovTest[0,0], visibilityPercent, 3) 

        # Mean and max gaps
        meanGapTest = covGenTestValues.coverageAnalysis.getTypeData("MEAN_GAP")
        maxGapTest = covGenTestValues.coverageAnalysis.getTypeData("MAX_GAP")

        listGaps = []
        for i, event in enumerate(totalListStates):
            date = totalListDates[i]
            if event == 'START':
                gapEnd = date
                if i == 0:
                    gapStart = initialDate
                listGaps.append(gapEnd.durationFrom(gapStart))
            elif event == 'END':
                gapStart = date
                if i == len(totalListStates)-1:
                    gapEnd = endDate
                    listGaps.append(gapEnd.durationFrom(gapStart))

        meanGap = np.mean(listGaps)
        maxGap = np.max(listGaps)
        self.assertTrue(abs(meanGap-meanGapTest[0,0]) <= 2.*optionsCov["step"])
        self.assertTrue(abs(maxGap-maxGapTest[0,0]) <= 2.*optionsCov["step"])
    

    def testValuesPolar(self):
        """
        Tests if four stations located at the four vertices of a unit region
        located near the North Pole would have the same combined visibility (satellite
        visible from at least one station) as the one computed with
        CoverageAnalysis.py.
        """

        sats = [
            {"name": "KepSat",
            "type": "keplerian",
            "sma": 7000000,
            "ecc": 0.007014455530245822,
            "inc": 89,
            "pa": 20,
            "raan": 15,
            "meanAnomaly": 10
            },
        ]

        optionsCov = {
            "timeStart": "2011-12-01T00:00:00",
            "timeEnd": "2011-12-02T00:00:00",
            "step": 1.,
            "elevation": 0,
            "nbSatsToCover": 1,
            "regionLatitudes": [89, 90],
            "regionLongitudes": [-111, -110],
            "plotType": "PERCENT_COV"
        }
    
        covGenTestValues = CoverageGenerator(self.celestialBody, sats)
        covGenTestValues.compute(optionsCov)
        percentCovTest = covGenTestValues.getTypeData()
        
        # Test using Keplerian coords file and visibility
        options = {"KEPLERIAN":{}}
        fileGenerator = FileGenerator(optionsCov["timeStart"], optionsCov["timeEnd"],
            optionsCov["step"], self.celestialBody, sats, [], options)

        dataFolder = 'test/files/'
        if not os.path.isdir(dataFolder):
            os.mkdir(dataFolder)
        fileGenerator.generate(dataFolder)
        
        satFileKep = dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        satKep = np.genfromtxt(satFileKep, skip_header=15)

        listLatitudes = [89., 89., 90., 90.]
        listLongitudes = [-120., -110., -111., -110.]
        listElevationDetector = []
        for i in range(4):
            latStation = FastMath.toRadians(listLatitudes[i])
            longStation = FastMath.toRadians(listLongitudes[i])
            altStation = 0.
            elevStation = FastMath.toRadians(float(optionsCov["elevation"]))

            station = GeodeticPoint(latStation, longStation, altStation)
            frameStation = TopocentricFrame(self.body, station, 'myStation')
            elevationDetector = ElevationDetector(frameStation)
            elevationDetector = elevationDetector.withConstantElevation(elevStation)
            listElevationDetector.append(elevationDetector)

        # Compute times
        mjd = np.trunc(satKep[:,0])
        seconds = satKep[:,1]
        initialDate = AbsoluteDate(optionsCov["timeStart"], self.utc)
        endDate = AbsoluteDate(optionsCov["timeEnd"], self.utc)

        listDates = []#[[], [], [], []]
        listStates = []#[[], [], [], []]
        valueVisOld = [0, 0, 0, 0]
        listIDStations = []#[[], [], [], []]

        for i in range(len(mjd)):
            # get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)

            # Find 0 of Elevation Detector function to get events
            sma = float(satKep[i,2])*1e3
            ecc = float(satKep[i,3])
            inc = FastMath.toRadians(float(satKep[i,4]))
            raan = FastMath.toRadians(float(satKep[i,5]))
            pa = FastMath.toRadians(float(satKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(satKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)

            for i in range(4):
                valueVis = listElevationDetector[i].g(
                    SpacecraftState(currentOrbit))

                if valueVisOld[i] < 0 and valueVis > 0:
                    listDates.append(absoluteDate)
                    listStates.append('START')
                    listIDStations.append(i)
                elif valueVisOld[i] > 0 and valueVis < 0:
                    listDates.append(absoluteDate)
                    listStates.append('END')
                    listIDStations.append(i)

                valueVisOld[i] = valueVis

        # Extract combined visibility of the four stations from visibility
        # of each station
        listStarted = []
        totalListDates = []
        totalListStates = []
        for i, date in enumerate(listDates):
            state = listStates[i]
            idStation = listIDStations[i]
            if len(listStarted) == 0:
                if state == 'END':
                    if len(totalListDates) != 0:
                        totalListDates = []
                        totalListStates = []
                    totalListDates.append(initialDate)
                    totalListStates.append('START')
                    totalListDates.append(date)
                    totalListStates.append('END')
                elif state == 'START':
                    totalListDates.append(date)
                    totalListStates.append('START')
                    listStarted.append(idStation)
            elif idStation not in listStarted:
                listStarted.append(idStation)
            elif len(listStarted) == 1 and idStation in listStarted:
                totalListDates.append(date)
                totalListStates.append('END')
                listStarted.remove(idStation)
            elif idStation in listStarted:
                listStarted.remove(idStation)
            else:
                raise ValueError

        # Percent coverage
        totalDuration = endDate.durationFrom(initialDate)
        visibilityDuration = 0.
        for i, event in enumerate(totalListStates):
            date = totalListDates[i]
            if event == 'START':
                initEvent = date
                if i == len(totalListStates)-1:
                    endEvent = endDate
                    visibilityDuration += endEvent.durationFrom(initEvent)
            else:
                endEvent = date
                if i == 0:
                    initEvent = initialDate
                visibilityDuration += endEvent.durationFrom(initEvent)

        visibilityPercent = visibilityDuration/totalDuration
        self.assertAlmostEqual(percentCovTest[0,0], visibilityPercent, 3) 

        # Mean and max gaps
        meanGapTest = covGenTestValues.coverageAnalysis.getTypeData("MEAN_GAP")
        maxGapTest = covGenTestValues.coverageAnalysis.getTypeData("MAX_GAP")

        listGaps = []
        for i, event in enumerate(totalListStates):
            date = totalListDates[i]
            if event == 'START':
                gapEnd = date
                if i == 0:
                    gapStart = initialDate
                listGaps.append(gapEnd.durationFrom(gapStart))
            elif event == 'END':
                gapStart = date
                if i == len(totalListStates)-1:
                    gapEnd = endDate
                    listGaps.append(gapEnd.durationFrom(gapStart))

        meanGap = np.mean(listGaps)
        maxGap = np.max(listGaps)
        self.assertTrue(abs(meanGap-meanGapTest[0,0]) <= 2.*optionsCov["step"])
        self.assertTrue(abs(maxGap-maxGapTest[0,0]) <= 2.*optionsCov["step"])

if __name__ == '__main__':   
    unittest.main()
