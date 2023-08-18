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
from org.orekit.frames import FramesFactory
from org.orekit.orbits import KeplerianOrbit, PositionAngle
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


class TestLLAEphemerides(unittest.TestCase):
    """
    Tests for generation of LLA ephemerides MEM files. This class tests
    if the files are correctly generated and if the data they contain are correct.
    """

    @classmethod
    def setUpClass(cls):
        """
        Generates Keplerian and LLA MEM files before tests with Earth
        as the central body, for two satellites, one defined with Keplerian
        coordinates and the other one with cartesian coordinates
        Keplerian MEM files are used to validate LLA MEM files.
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
        cls.groundStations = []

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
        cls.kepSat = cls.satellites[0]
        cls.cartSat = cls.satellites[1]
        cls.utc = TimeScalesFactory.getUTC()

        options = {"KEPLERIAN":{}, "LLA":{}}
        fileGenerator = FileGenerator(cls.startDate, cls.endDate, cls.step,
            cls.celestialBody, cls.satellites, cls.groundStations, options)

        if not os.path.isdir(cls.dataFolder):
            os.mkdir(cls.dataFolder)
        fileGenerator.generate(cls.dataFolder)

    def testLLA(self):
        """
        Tests if the LLA MEM files have correctly been created
        """

        KepSatFileLLA = self.dataFolder+'KepSat_MEM_LLA.TXT'
        CartSatFileLLA = self.dataFolder+'CartSat_MEM_LLA.TXT'
        # Do files exist?
        self.assertTrue(os.path.exists(KepSatFileLLA))
        self.assertTrue(os.path.exists(CartSatFileLLA))

    def testLLAKepSatDates(self):  
        """
        Tests if the start and end dates are correctly computed for the
        Keplerian satellite
        """

        KepSatFileLLA = self.dataFolder+'KepSat_MEM_LLA.TXT'
        KepSatLLA = np.genfromtxt(KepSatFileLLA, skip_header=15)

        # Does it begin and end at right dates?
        mjd = int(np.trunc(KepSatLLA[0,0]))
        seconds = float(KepSatLLA[0,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)
        self.assertTrue(dateTime.equals(dateTimeStart))

        mjd = int(np.trunc(KepSatLLA[-1,0]))
        seconds = float(KepSatLLA[-1,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeEnd = DateTimeComponents.parseDateTime(self.endDate)
        self.assertTrue(dateTime.equals(dateTimeEnd))
    
    def testLLACartSatDates(self):  
        """
        Tests if the start and end dates are correctly computed for the
        cartesian satellite
        """

        CartSatFileLLA = self.dataFolder+'CartSat_MEM_LLA.TXT'
        CartSatLLA = np.genfromtxt(CartSatFileLLA, skip_header=15)

        # Does it begin and end at right dates?
        mjd = int(np.trunc(CartSatLLA[0,0]))
        seconds = float(CartSatLLA[0,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)
        self.assertTrue(dateTime.equals(dateTimeStart))

        mjd = int(np.trunc(CartSatLLA[-1,0]))
        seconds = float(CartSatLLA[-1,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeEnd = DateTimeComponents.parseDateTime(self.endDate)
        self.assertTrue(dateTime.equals(dateTimeEnd))

    def testLLAKepSat(self):
        """
        Tests if the LLA coordinates are correctly computed for the
        Keplerian satellite
        """

        KepSatFileLLA = self.dataFolder+'KepSat_MEM_LLA.TXT'
        KepSatLLA = np.genfromtxt(KepSatFileLLA, skip_header=15)

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        # Test if files have same length
        self.assertTrue(len(KepSatLLA[:,0]) == len(KepSatKep[:,0]))

        # Compute times
        mjd = np.trunc(KepSatLLA[:,0])
        seconds = KepSatLLA[:,1]
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        # Compute LLA from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Get Cart coordinates
            sma = float(KepSatKep[i,2])*1e3
            ecc = float(KepSatKep[i,3])
            inc = FastMath.toRadians(float(KepSatKep[i,4]))
            raan = FastMath.toRadians(float(KepSatKep[i,5]))
            pa = FastMath.toRadians(float(KepSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(KepSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            currentPosition = currentOrbit.getPVCoordinates().getPosition()
            point = self.body.transform(currentPosition, self.inertialFrame,
                absoluteDate)
            latCur = FastMath.toDegrees(point.getLatitude()) # in deg
            longCur = FastMath.toDegrees(point.getLongitude()) # in deg
            altCur = point.getAltitude() * 1e-3 # in km

            self.assertAlmostEqual(KepSatLLA[i,2], latCur, 3)
            self.assertAlmostEqual(KepSatLLA[i,3], longCur, 3)
            self.assertAlmostEqual(KepSatLLA[i,4], altCur, 3)

    def testLLACartSat(self):
        """
        Tests if the LLA coordinates are correctly computed for the
        cartesian satellite
        """

        CartSatFileLLA = self.dataFolder+'CartSat_MEM_LLA.TXT'
        CartSatLLA = np.genfromtxt(CartSatFileLLA, skip_header=15)

        CartSatFileKep = self.dataFolder+'CartSat_MEM_KEPLERIAN.TXT'
        CartSatKep = np.genfromtxt(CartSatFileKep, skip_header=15)

        # Test if files have same length
        self.assertTrue(len(CartSatLLA[:,0]) == len(CartSatKep[:,0]))

        # Compute times
        mjd = np.trunc(CartSatLLA[:,0])
        seconds = CartSatLLA[:,1]
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        # Compute LLA from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Get Cart coordinates
            sma = float(CartSatKep[i,2])*1e3
            ecc = float(CartSatKep[i,3])
            inc = FastMath.toRadians(float(CartSatKep[i,4]))
            raan = FastMath.toRadians(float(CartSatKep[i,5]))
            pa = FastMath.toRadians(float(CartSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(CartSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            currentPosition = currentOrbit.getPVCoordinates().getPosition()
            point = self.body.transform(currentPosition, self.inertialFrame,
                absoluteDate)

            latCur = FastMath.toDegrees(point.getLatitude()) # in deg
            longCur = FastMath.toDegrees(point.getLongitude()) # in deg
            altCur = point.getAltitude() * 1e-3 # in km

            self.assertAlmostEqual(CartSatLLA[i,2], latCur, 3)
            self.assertAlmostEqual(CartSatLLA[i,3], longCur, 3)
            self.assertAlmostEqual(CartSatLLA[i,4], altCur, 3)

if __name__ == '__main__':   
    unittest.main()
