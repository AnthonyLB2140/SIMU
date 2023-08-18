import orekit
vm = orekit.initVM()

from datetime import datetime
import traceback
import unittest
import sys
import os
import numpy as np

from org.hipparchus.util import FastMath

from org.orekit.bodies import CelestialBodyFactory
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

class TestCartesianEphemerides(unittest.TestCase):
    """
    Tests for generation of cartesian ephemerides OEM files. This class tests
    if the files are correctly generated and if the data they contain are correct.
    Examples are provided for Earth and Mars, since OEM CIC files require
    an additional rotation for non-Earth bodies in order to use EME2000 axes.
    """

    @classmethod
    def setUpClass(cls):
        """
        Generates Keplerian MEM and Cartesian OEM files before tests with Earth
        as the central body, for two satellites, one defined with Keplerian
        coordinates and the other one with cartesian coordinates
        Keplerian MEM files are used to validate OEM files.
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
            cls.inertialFrame = FramesFactory.getEME2000()
        else:
            cls.inertialFrame = celestialBody.getInertiallyOrientedFrame()

        cls.mu = CelestialBodyFactory.getBody(cls.celestialBody).getGM()

        cls.dataFolder = 'test/files/'
        cls.kepSat = cls.satellites[0]
        cls.cartSat = cls.satellites[1]
        cls.utc = TimeScalesFactory.getUTC()

        options = {"KEPLERIAN":{}, "CARTESIAN":{}}
        fileGenerator = FileGenerator(cls.startDate, cls.endDate, cls.step,
            cls.celestialBody, cls.satellites, cls.groundStations, options)

        if not os.path.isdir(cls.dataFolder):
            os.mkdir(cls.dataFolder)
        fileGenerator.generate(cls.dataFolder)

    def testCartesian(self):
        """
        Tests if the cartesian files have correctly been created
        """

        KepSatFileCart = self.dataFolder+'KepSat_OEM_POSITION.TXT'
        CartSatFileCart = self.dataFolder+'CartSat_OEM_POSITION.TXT'
        # Do files exist?
        self.assertTrue(os.path.exists(KepSatFileCart))
        self.assertTrue(os.path.exists(CartSatFileCart))

    def testCartesianKepSatDates(self):  
        """
        Tests if the start and end dates are correctly computed for
        the Keplerian satellite
        """

        KepSatFileCart = self.dataFolder+'KepSat_OEM_POSITION.TXT'
        KepSatCart = np.genfromtxt(KepSatFileCart, skip_header=20)

        # Does it begin and end at right dates?
        mjd = int(np.trunc(KepSatCart[0,0]))
        seconds = float(KepSatCart[0,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)
        self.assertTrue(dateTime.equals(dateTimeStart))

        mjd = int(np.trunc(KepSatCart[-1,0]))
        seconds = float(KepSatCart[-1,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeEnd = DateTimeComponents.parseDateTime(self.endDate)
        self.assertTrue(dateTime.equals(dateTimeEnd))
    
    def testCartesianCartSatDates(self):
        """
        Tests if the start and end dates are correctly computed for
        the Cartesian satellite
        """

        CartSatFileCart = self.dataFolder+'CartSat_OEM_POSITION.TXT'
        CartSatCart = np.genfromtxt(CartSatFileCart, skip_header=20)

        # Does it begin and end at right dates?
        mjd = int(np.trunc(CartSatCart[0,0]))
        seconds = float(CartSatCart[0,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)
        self.assertTrue(dateTime.equals(dateTimeStart))

        mjd = int(np.trunc(CartSatCart[-1,0]))
        seconds = float(CartSatCart[-1,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeEnd = DateTimeComponents.parseDateTime(self.endDate)
        self.assertTrue(dateTime.equals(dateTimeEnd))

    def testCartKepSat(self):
        """
        Tests if the cartesian coordinates are correctly computed for the
        Keplerian satellite
        """

        KepSatFileCart = self.dataFolder+'KepSat_OEM_POSITION.TXT'
        KepSatCart = np.genfromtxt(KepSatFileCart, skip_header=20)

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        # Test if files have same length
        self.assertTrue(len(KepSatCart[:,0]) == len(KepSatKep[:,0]))

        # Compute times
        mjd = np.trunc(KepSatCart[:,0])
        seconds = KepSatCart[:,1]
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        # Convert in m and m/s
        KepSatCart[:,2:] = KepSatCart[:,2:] * 1e3

        # Compute Cart from Kep coords
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
            PosCur = currentOrbit.getPVCoordinates().getPosition()
            xCur, yCur, zCur = (PosCur.getX(), PosCur.getY(), PosCur.getZ())
            VelCur = currentOrbit.getPVCoordinates().getVelocity()
            vxCur, vyCur, vzCur = (VelCur.getX(), VelCur.getY(), VelCur.getZ())

            self.assertAlmostEqual(KepSatCart[i,2], xCur, 1)
            self.assertAlmostEqual(KepSatCart[i,3], yCur, 1)
            self.assertAlmostEqual(KepSatCart[i,4], zCur, 1)
            self.assertAlmostEqual(KepSatCart[i,5], vxCur, 1)
            self.assertAlmostEqual(KepSatCart[i,6], vyCur, 1)
            self.assertAlmostEqual(KepSatCart[i,7], vzCur, 1)

    def testCartCartSat(self):
        """
        Tests if the cartesian coordinates are correctly computed for the
        cartesian satellite
        """

        CartSatFileCart = self.dataFolder+'CartSat_OEM_POSITION.TXT'
        CartSatCart = np.genfromtxt(CartSatFileCart, skip_header=20)

        CartSatFileKep = self.dataFolder+'CartSat_MEM_KEPLERIAN.TXT'
        CartSatKep = np.genfromtxt(CartSatFileKep, skip_header=15)

        # Test if files have same length
        self.assertTrue(len(CartSatCart[:,0]) == len(CartSatKep[:,0]))

        # Compute times
        mjd = np.trunc(CartSatCart[:,0])
        seconds = CartSatCart[:,1]
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        # Convert in m and m/s
        CartSatCart[:,2:] = CartSatCart[:,2:] * 1e3

        # Compute Cart from Kep coords
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
            PosCur = currentOrbit.getPVCoordinates().getPosition()
            xCur, yCur, zCur = (PosCur.getX(), PosCur.getY(), PosCur.getZ())
            VelCur = currentOrbit.getPVCoordinates().getVelocity()
            vxCur, vyCur, vzCur = (VelCur.getX(), VelCur.getY(), VelCur.getZ())

            self.assertAlmostEqual(CartSatCart[i,2], xCur, 1)
            self.assertAlmostEqual(CartSatCart[i,3], yCur, 1)
            self.assertAlmostEqual(CartSatCart[i,4], zCur, 1)
            self.assertAlmostEqual(CartSatCart[i,5], vxCur, 1)
            self.assertAlmostEqual(CartSatCart[i,6], vyCur, 1)
            self.assertAlmostEqual(CartSatCart[i,7], vzCur, 1)

    def testCartMars(self):
        """
        Tests if the cartesian coordinates are correctly computed for a
        Martian Keplerian satellite
        """

        header = {
            "mission": "validationMars",
            "celestialBody": "MARS",
            "timeStart": "2000-01-01T12:00:00",
            "timeEnd": "2000-01-02T12:00:00",
            "step": "10"
        }
        satellites = [
            {"name": "MarsSat",
            "type": "keplerian",
            "sma": 7000000,
            "ecc": 0.007014455530245822,
            "inc": 51,
            "pa": 20,
            "raan": 15,
            "meanAnomaly": 10
            }
        ]
        groundStations = []

        step = float( header['step'] )
        startDate = str( header['timeStart'] )
        endDate = str( header['timeEnd'] )
        stringBody = str( header['celestialBody'] )
        
        celestialBody = CelestialBodyFactory.getBody(stringBody)
        inertialFrameBody = celestialBody.getInertiallyOrientedFrame()
        mu = CelestialBodyFactory.getBody(stringBody).getGM()

        inertialFrameEarth = FramesFactory.getEME2000()

        options = {"KEPLERIAN":{}, "CARTESIAN":{}}
        fileGeneratorMars = FileGenerator(startDate, endDate, step,
            stringBody, satellites, groundStations, options)

        if not os.path.isdir(self.dataFolder):
            os.mkdir(self.dataFolder)
        fileGeneratorMars.generate(self.dataFolder)

        MarsSatFileCart = self.dataFolder+'MarsSat_OEM_POSITION.TXT'
        MarsSatCart = np.genfromtxt(MarsSatFileCart, skip_header=20)

        MarsSatFileKep = self.dataFolder+'MarsSat_MEM_KEPLERIAN.TXT'
        MarsSatKep = np.genfromtxt(MarsSatFileKep, skip_header=15)

        # Compute times
        mjd = np.trunc(MarsSatCart[:,0])
        seconds = MarsSatCart[:,1]
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        # Convert in m and m/s
        MarsSatCart[:,2:] = MarsSatCart[:,2:] * 1e3

        # Compute Cart from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Get Cart coordinates
            sma = float(MarsSatKep[i,2])*1e3
            ecc = float(MarsSatKep[i,3])
            inc = FastMath.toRadians(float(MarsSatKep[i,4]))
            raan = FastMath.toRadians(float(MarsSatKep[i,5]))
            pa = FastMath.toRadians(float(MarsSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(MarsSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, inertialFrameBody, absoluteDate, mu)
            PosCur = currentOrbit.getPVCoordinates().getPosition()
            VelCur = currentOrbit.getPVCoordinates().getVelocity()

            # Rotation to EME axes, since CIC files require this frame
            transform = inertialFrameBody.getTransformTo(inertialFrameEarth,
                absoluteDate)
            rotationBodyEME = transform.getRotation()
            newPosCur = rotationBodyEME.applyTo(PosCur)
            newVelCur = rotationBodyEME.applyTo(VelCur)

            xCur, yCur, zCur = (newPosCur.getX(), newPosCur.getY(), newPosCur.getZ())
            vxCur, vyCur, vzCur = (newVelCur.getX(), newVelCur.getY(), newVelCur.getZ())

            self.assertAlmostEqual(MarsSatCart[i,2], xCur, 0)
            self.assertAlmostEqual(MarsSatCart[i,3], yCur, 0)
            self.assertAlmostEqual(MarsSatCart[i,4], zCur, 0)
            self.assertAlmostEqual(MarsSatCart[i,5], vxCur, 0)
            self.assertAlmostEqual(MarsSatCart[i,6], vyCur, 0)
            self.assertAlmostEqual(MarsSatCart[i,7], vzCur, 0)


    
if __name__ == '__main__':   
    unittest.main()
