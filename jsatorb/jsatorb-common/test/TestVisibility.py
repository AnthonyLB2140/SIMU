import orekit
vm = orekit.initVM()

from datetime import datetime
import traceback
import unittest
import sys
import os
import numpy as np

from org.hipparchus.util import FastMath

from org.orekit.bodies import OneAxisEllipsoid, CelestialBodyFactory, GeodeticPoint
from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.events import ElevationDetector
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.time import DateTimeComponents, DateComponents, TimeComponents
from org.orekit.utils import IERSConventions, PVCoordinates

sys.path.append('src')
sys.path.append('src/VTS')
sys.path.append('src/MEM')
sys.path.append('src/AEM')
sys.path.append('src/file-conversion')
sys.path.append('../jsatorb-visibility-service/src')

from ListCelestialBodies import ListCelestialBodies
from FileGenerator import FileGenerator

class TestVisibility(unittest.TestCase):
    """
    Tests for generation of visibility MEM files. This class tests if the files
    are correctly generated and if the data they contain are correct.
    """

    @classmethod
    def setUpClass(cls):
        """
        Generates Keplerian and Visibility MEM files before tests with Earth
        as the central body, for two satellites, one defined with keplerian
        coordinates and the other one with cartesian coordinates, and for
        two ground stations
        The Keplerian MEM files are used to validate visibility MEM files.
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
        cls.groundStations = [
            {"name": "sydney",
            "latitude": -33.8678500,
            "longitude": 151.2073200,
            "altitude": 58,
            "elevation": 0.5
            },
            {"name": "isae",
            "latitude": 43,
            "longitude": 1.5,
            "altitude": 150,
            "elevation": 30
            }
        ]
        cls.step = float( header['step'] )
        cls.startDate = str( header['timeStart'] )
        cls.endDate = str( header['timeEnd'] )
        cls.celestialBody = str( header['celestialBody'] )
        
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
        cls.mu = CelestialBodyFactory.getBody(cls.celestialBody).getGM()

        cls.dataFolder = 'test/files/'
        cls.sydney = cls.groundStations[0]
        cls.isae = cls.groundStations[1]
        cls.utc = TimeScalesFactory.getUTC()

        options = {"KEPLERIAN":{}, "VISIBILITY":{}}
        fileGenerator = FileGenerator(cls.startDate, cls.endDate, cls.step,
            cls.celestialBody, cls.satellites, cls.groundStations, options)

        if not os.path.isdir(cls.dataFolder):
            os.mkdir(cls.dataFolder)
        fileGenerator.generate(cls.dataFolder)

    def testVisibility(self):
        """
        Tests if the visibility files have correctly been created
        """

        KepSatFileVisIsae = self.dataFolder+'KepSat_MEM_VISIBILITY_isae.TXT'
        CartSatFileVisIsae = self.dataFolder+'CartSat_MEM_VISIBILITY_isae.TXT'
        KepSatFileVisSydney = self.dataFolder+'KepSat_MEM_VISIBILITY_sydney.TXT'
        CartSatFileVisSydney = self.dataFolder+'CartSat_MEM_VISIBILITY_sydney.TXT'

        # Do files exist?
        self.assertTrue(os.path.exists(KepSatFileVisIsae))
        self.assertTrue(os.path.exists(CartSatFileVisIsae))
        self.assertTrue(os.path.exists(KepSatFileVisSydney))
        self.assertTrue(os.path.exists(CartSatFileVisSydney))
    
    def testVisibilityKepSatIsae(self):
        """
        Tests if the visibility dates are correctly computed for the Keplerian
        satellite and the Isae station
        """

        KepSatFileVisIsae = self.dataFolder+'KepSat_MEM_VISIBILITY_isae.TXT'
        KepSatVisIsae = np.genfromtxt(KepSatFileVisIsae, skip_header=15)[:,:2]
        KepSatVisIsaeStates = np.genfromtxt(KepSatFileVisIsae, delimiter=' ',
            skip_header=15, usecols=2, dtype=str)

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        nameStation = self.isae["name"]
        latStation = FastMath.toRadians(float(self.isae["latitude"]))
        longStation = FastMath.toRadians(float(self.isae["longitude"]))
        altStation = float(self.isae["altitude"])
        elevStation = FastMath.toRadians(float(self.isae["elevation"]))

        station = GeodeticPoint(latStation, longStation, altStation)
        frameStation = TopocentricFrame(self.body, station, nameStation)
        elevationDetector = ElevationDetector(frameStation)
        elevationDetector = elevationDetector.withConstantElevation(elevStation)
                
        # Compute times
        mjd = np.trunc(KepSatKep[:,0])
        seconds = KepSatKep[:,1]
        listDates = []
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        listStates = []
        valueVisOld = 0
        # Compute visibilities from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Find 0 of Elevation Detector function to get events
            sma = float(KepSatKep[i,2])*1e3
            ecc = float(KepSatKep[i,3])
            inc = FastMath.toRadians(float(KepSatKep[i,4]))
            raan = FastMath.toRadians(float(KepSatKep[i,5]))
            pa = FastMath.toRadians(float(KepSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(KepSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            valueVis = elevationDetector.g(SpacecraftState(currentOrbit))

            if valueVisOld < 0 and valueVis > 0:
                listDates.append(absoluteDate)
                listStates.append('START')
            elif valueVisOld > 0 and valueVis < 0:
                listDates.append(absoluteDate)
                listStates.append('END')

            valueVisOld = valueVis
        
        # Check if same number of events
        self.assertEqual(len(KepSatVisIsae[:,0]), len(listStates))
        for i in range(len(KepSatVisIsae[:,0])):
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH,
                int(KepSatVisIsae[i,0]))
            time = TimeComponents(float(KepSatVisIsae[i,1]))
            dateVisCur = AbsoluteDate(date, time, self.utc)

            # Check if same dates for events
            self.assertTrue(abs(dateVisCur.durationFrom(listDates[i])) < self.step)
            
            # Check if same types of events
            self.assertEqual(KepSatVisIsaeStates[i], listStates[i])

    def testVisibilityKepSatSydney(self):
        """
        Tests if the visibility dates are correctly computed for the Keplerian
        satellite and the Sydney station
        """

        KepSatFileVisSydney = self.dataFolder+'KepSat_MEM_VISIBILITY_sydney.TXT'
        KepSatVisSydney = np.genfromtxt(KepSatFileVisSydney, skip_header=15)[:,:2]
        KepSatVisSydneyStates = np.genfromtxt(KepSatFileVisSydney, delimiter=' ',
            skip_header=15, usecols=2, dtype=str)

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        nameStation = self.sydney["name"]
        latStation = FastMath.toRadians(float(self.sydney["latitude"]))
        longStation = FastMath.toRadians(float(self.sydney["longitude"]))
        altStation = float(self.sydney["altitude"])
        elevStation = FastMath.toRadians(float(self.sydney["elevation"]))

        station = GeodeticPoint(latStation, longStation, altStation)
        frameStation = TopocentricFrame(self.body, station, nameStation)
        elevationDetector = ElevationDetector(frameStation)
        elevationDetector = elevationDetector.withConstantElevation(elevStation)
                
        # Compute times
        mjd = np.trunc(KepSatKep[:,0])
        seconds = KepSatKep[:,1]
        listDates = []
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        listStates = []
        valueVisOld = 0
        # Compute visibilities from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Find 0 of Elevation Detector function to get events
            sma = float(KepSatKep[i,2])*1e3
            ecc = float(KepSatKep[i,3])
            inc = FastMath.toRadians(float(KepSatKep[i,4]))
            raan = FastMath.toRadians(float(KepSatKep[i,5]))
            pa = FastMath.toRadians(float(KepSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(KepSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            valueVis = elevationDetector.g(SpacecraftState(currentOrbit))

            if valueVisOld < 0 and valueVis > 0:
                listDates.append(absoluteDate)
                listStates.append('START')
            elif valueVisOld > 0 and valueVis < 0:
                listDates.append(absoluteDate)
                listStates.append('END')

            valueVisOld = valueVis
        
        # Check if same number of events
        self.assertEqual(len(KepSatVisSydney[:,0]), len(listStates))
        for i in range(len(KepSatVisSydney[:,0])):
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH,
                int(KepSatVisSydney[i,0]))
            time = TimeComponents(float(KepSatVisSydney[i,1]))
            dateVisCur = AbsoluteDate(date, time, self.utc)

            # Check if same dates for events
            self.assertTrue(abs(dateVisCur.durationFrom(listDates[i])) < self.step)
            
            # Check if same types of events
            self.assertEqual(KepSatVisSydneyStates[i], listStates[i])

    def testVisibilityCartSatIsae(self):
        """
        Tests if the visibility dates are correctly computed for the cartesian
        satellite and the Isae station
        """

        CartSatFileVisIsae = self.dataFolder+'CartSat_MEM_VISIBILITY_isae.TXT'
        CartSatVisIsae = np.genfromtxt(CartSatFileVisIsae, skip_header=15)[:,:2]
        CartSatVisIsaeStates = np.genfromtxt(CartSatFileVisIsae, delimiter=' ',
            skip_header=15, usecols=2, dtype=str)

        CartSatFileKep = self.dataFolder+'CartSat_MEM_KEPLERIAN.TXT'
        CartSatKep = np.genfromtxt(CartSatFileKep, skip_header=15)

        nameStation = self.isae["name"]
        latStation = FastMath.toRadians(float(self.isae["latitude"]))
        longStation = FastMath.toRadians(float(self.isae["longitude"]))
        altStation = float(self.isae["altitude"])
        elevStation = FastMath.toRadians(float(self.isae["elevation"]))

        station = GeodeticPoint(latStation, longStation, altStation)
        frameStation = TopocentricFrame(self.body, station, nameStation)
        elevationDetector = ElevationDetector(frameStation)
        elevationDetector = elevationDetector.withConstantElevation(elevStation)
                
        # Compute times
        mjd = np.trunc(CartSatKep[:,0])
        seconds = CartSatKep[:,1]
        listDates = []
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        listStates = []
        valueVisOld = 0
        # Compute visibilities from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Find 0 of Elevation Detector function to get events
            sma = float(CartSatKep[i,2])*1e3
            ecc = float(CartSatKep[i,3])
            inc = FastMath.toRadians(float(CartSatKep[i,4]))
            raan = FastMath.toRadians(float(CartSatKep[i,5]))
            pa = FastMath.toRadians(float(CartSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(CartSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            valueVis = elevationDetector.g(SpacecraftState(currentOrbit))

            if valueVisOld < 0 and valueVis > 0:
                listDates.append(absoluteDate)
                listStates.append('START')
            elif valueVisOld > 0 and valueVis < 0:
                listDates.append(absoluteDate)
                listStates.append('END')

            valueVisOld = valueVis
        
        # Check if same number of events
        self.assertEqual(len(CartSatVisIsae[:,0]), len(listStates))
        for i in range(len(CartSatVisIsae[:,0])):
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH,
                int(CartSatVisIsae[i,0]))
            time = TimeComponents(float(CartSatVisIsae[i,1]))
            dateVisCur = AbsoluteDate(date, time, self.utc)

            # Check if same dates for events
            self.assertTrue(abs(dateVisCur.durationFrom(listDates[i])) < self.step)
            
            # Check if same types of events
            self.assertEqual(CartSatVisIsaeStates[i], listStates[i])

    def testVisibilityCartSatSydney(self):
        """
        Tests if the visibility dates are correctly computed for the cartesian
        satellite and the Sydney station
        """

        CartSatFileVisSydney = self.dataFolder+'CartSat_MEM_VISIBILITY_sydney.TXT'
        CartSatVisSydney = np.genfromtxt(CartSatFileVisSydney, skip_header=15)[:,:2]
        CartSatVisSydneyStates = np.genfromtxt(CartSatFileVisSydney, delimiter=' ',
            skip_header=15, usecols=2, dtype=str)

        CartSatFileKep = self.dataFolder+'CartSat_MEM_KEPLERIAN.TXT'
        CartSatKep = np.genfromtxt(CartSatFileKep, skip_header=15)

        nameStation = self.sydney["name"]
        latStation = FastMath.toRadians(float(self.sydney["latitude"]))
        longStation = FastMath.toRadians(float(self.sydney["longitude"]))
        altStation = float(self.sydney["altitude"])
        elevStation = FastMath.toRadians(float(self.sydney["elevation"]))

        station = GeodeticPoint(latStation, longStation, altStation)
        frameStation = TopocentricFrame(self.body, station, nameStation)
        elevationDetector = ElevationDetector(frameStation)
        elevationDetector = elevationDetector.withConstantElevation(elevStation)
                
        # Compute times
        mjd = np.trunc(CartSatKep[:,0])
        seconds = CartSatKep[:,1]
        listDates = []
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        listStates = []
        valueVisOld = 0
        # Compute visibilities from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Find 0 of Elevation Detector function to get events
            sma = float(CartSatKep[i,2])*1e3
            ecc = float(CartSatKep[i,3])
            inc = FastMath.toRadians(float(CartSatKep[i,4]))
            raan = FastMath.toRadians(float(CartSatKep[i,5]))
            pa = FastMath.toRadians(float(CartSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(CartSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            valueVis = elevationDetector.g(SpacecraftState(currentOrbit))

            if valueVisOld < 0 and valueVis > 0:
                listDates.append(absoluteDate)
                listStates.append('START')
            elif valueVisOld > 0 and valueVis < 0:
                listDates.append(absoluteDate)
                listStates.append('END')

            valueVisOld = valueVis
        
        # Check if same number of events
        self.assertEqual(len(CartSatVisSydney[:,0]), len(listStates))
        for i in range(len(CartSatVisSydney[:,0])):
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH,
                int(CartSatVisSydney[i,0]))
            time = TimeComponents(float(CartSatVisSydney[i,1]))
            dateVisCur = AbsoluteDate(date, time, self.utc)

            # Check if same dates for events
            self.assertTrue(abs(dateVisCur.durationFrom(listDates[i])) < self.step)
            
            # Check if same types of events
            self.assertEqual(CartSatVisSydneyStates[i], listStates[i])    

if __name__ == '__main__':   
    unittest.main()
