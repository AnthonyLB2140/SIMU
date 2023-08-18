import orekit
vm = orekit.initVM()

from datetime import datetime
import traceback
import unittest
import sys
import os
import numpy as np

from org.hipparchus.geometry.euclidean.threed import Vector3D, RotationOrder
from org.hipparchus.util import FastMath

from org.orekit.bodies import CelestialBodyFactory
from org.orekit.frames import FramesFactory
from org.orekit.orbits import KeplerianOrbit
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.time import DateTimeComponents, DateComponents, TimeComponents
from org.orekit.utils import PVCoordinates

sys.path.append('src')
sys.path.append('src/VTS')
sys.path.append('src/MEM')
sys.path.append('src/AEM')
sys.path.append('src/file-conversion')
sys.path.append('../jsatorb-visibility-service/src')

from FileGenerator import FileGenerator

class TestKeplerianEphemerides(unittest.TestCase):
    """
    Tests for generation of Keplerian ephemerides MEM files. This class tests
    if the files are correctly generated and if the data they contain are correct.
    """

    @classmethod
    def setUpClass(cls):
        """
        Generates Keplerian MEM files before tests with Earth as the central body,
        for two satellites, one defined with Keplerian coordinates and the other
        one with cartesian coordinates
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
        cls.dataFolder = 'test/files/'
        cls.kepSat = cls.satellites[0]
        cls.cartSat = cls.satellites[1]

        options = {"KEPLERIAN":{}}
        fileGenerator = FileGenerator(cls.startDate, cls.endDate, cls.step,
            cls.celestialBody, cls.satellites, cls.groundStations, options)
            
        if not os.path.isdir(cls.dataFolder):
            os.mkdir(cls.dataFolder)
        fileGenerator.generate(cls.dataFolder)

    def testKeplerianCoordinates(self):  
        """
        Tests if the Keplerian files have correctly been created
        """     

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        CartSatFileKep = self.dataFolder+'CartSat_MEM_KEPLERIAN.TXT'
        # Do files exist?
        self.assertTrue(os.path.exists(KepSatFileKep))
        self.assertTrue(os.path.exists(CartSatFileKep))
    
    def testKeplerianCoordinatesDates(self): 
        """
        Tests if the start and end dates are correctly computed for
        the Keplerian satellite
        """

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKeplerian = np.genfromtxt(KepSatFileKep, skip_header=15)

        # Does it begin and end at right dates?
        mjd = int(np.trunc(KepSatKeplerian[0,0]))
        seconds = float(KepSatKeplerian[0,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)
        self.assertTrue(dateTime.equals(dateTimeStart))

        mjd = int(np.trunc(KepSatKeplerian[-1,0]))
        seconds = float(KepSatKeplerian[-1,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeEnd = DateTimeComponents.parseDateTime(self.endDate)
        self.assertTrue(dateTime.equals(dateTimeEnd))

    def testKeplerianCoordinatesSMA(self):
        """
        Tests if the semi-major axis is constant and equal to the given value,
        for the Keplerian satellite
        """

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKeplerian = np.genfromtxt(KepSatFileKep, skip_header=15)

        sma = KepSatKeplerian[:,2]*1e3 # in m
        self.assertAlmostEqual(np.min(sma), np.max(sma), 3)
        self.assertAlmostEqual(np.mean(sma), float(self.kepSat['sma']), 3)
    
    def testKeplerianCoordinatesEcc(self):
        """
        Tests if the eccentricity is constant and equal to the given value,
        for the Keplerian satellite
        """

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKeplerian = np.genfromtxt(KepSatFileKep, skip_header=15)

        ecc = KepSatKeplerian[:,3]
        self.assertAlmostEqual(np.min(ecc), np.max(ecc), 3)
        self.assertAlmostEqual(np.mean(ecc), float(self.kepSat['ecc']), 3)

    def testKeplerianCoordinatesInc(self):
        """
        Tests if the inclination is constant and equal to the given value,
        for the Keplerian satellite
        """

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKeplerian = np.genfromtxt(KepSatFileKep, skip_header=15)

        inc = KepSatKeplerian[:,4]
        self.assertAlmostEqual(np.min(inc), np.max(inc), 3)
        self.assertAlmostEqual(np.mean(inc), float(self.kepSat['inc']), 3)

    def testKeplerianCoordinatesRAAN(self):
        """
        Tests if the right ascension of the ascending node (RAAN) is 
        constant and equal to the given value, for the Keplerian satellite
        """

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKeplerian = np.genfromtxt(KepSatFileKep, skip_header=15)

        raan = KepSatKeplerian[:,5]
        raan[raan<-180] = raan[raan<-180]+360
        raan[raan>180] = raan[raan>180]-360
        self.assertAlmostEqual(np.min(raan), np.max(raan), 3)
        self.assertAlmostEqual(np.mean(raan), float(self.kepSat['raan']), 3)

    def testKeplerianCoordinatesPA(self):
        """
        Tests if the argument of periapsis (PA) is constant and equal to the
        given value, for the Keplerian satellite
        """

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKeplerian = np.genfromtxt(KepSatFileKep, skip_header=15)

        pa = KepSatKeplerian[:,6]
        pa[pa<-180] = pa[pa<-180]+360
        pa[pa>180] = pa[pa>180]-360
        self.assertAlmostEqual(np.min(pa), np.max(pa), 3)
        self.assertAlmostEqual(np.mean(pa), float(self.kepSat['pa']), 3)

    def testKeplerianCoordinatesMA(self):
        """
        Tests if the mean anomaly is correct, for the Keplerian satellite
        """

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKeplerian = np.genfromtxt(KepSatFileKep, skip_header=15)

        # Compute times
        mjd = np.trunc(KepSatKeplerian[:,0])
        seconds = KepSatKeplerian[:,1]
        times = []
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        # Compute analytic mean anomalies, from SMA and central body's mu
        for i in range(len(mjd)):
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            dateTime = DateTimeComponents(date, time)
            times.append( dateTime.offsetFrom(dateTimeStart) )
        times = np.array(times)

        mu = CelestialBodyFactory.getBody(self.celestialBody).getGM()
        a = float(self.kepSat['sma'])
        ma_analytic = np.rad2deg((mu/a**3)**0.5)*times + float(self.kepSat['meanAnomaly'])
        ma_analytic = np.mod(ma_analytic, 360)
        ma_analytic[ma_analytic>180] = ma_analytic[ma_analytic>180]-360
        ma_analytic[ma_analytic<-180] = ma_analytic[ma_analytic<-180]+360

        ma = KepSatKeplerian[:,7]
        self.assertTrue(np.all(np.abs(ma - ma_analytic) < 1e-3))

    def testKeplerianCoordinatesCartDates(self): 
        """
        Tests if the start and end dates are correctly computed for
        the cartesian satellite
        """

        CartSatFileKep = self.dataFolder+'CartSat_MEM_KEPLERIAN.TXT'
        CartSatKeplerian = np.genfromtxt(CartSatFileKep, skip_header=15)

        # Does it begin and end at right dates?
        mjd = int(np.trunc(CartSatKeplerian[0,0]))
        seconds = float(CartSatKeplerian[0,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)
        self.assertTrue(dateTime.equals(dateTimeStart))

        mjd = int(np.trunc(CartSatKeplerian[-1,0]))
        seconds = float(CartSatKeplerian[-1,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeEnd = DateTimeComponents.parseDateTime(self.endDate)
        self.assertTrue(dateTime.equals(dateTimeEnd))

    def testKeplerianCoordinatesCart(self):
        """
        Tests if the Keplerian coordinates are correct and constant (except for 
        the mean anomaly), for the cartesian satellite
        """

        CartSatFileKep = self.dataFolder+'CartSat_MEM_KEPLERIAN.TXT'
        CartSatKeplerian = np.genfromtxt(CartSatFileKep, skip_header=15)

        position = Vector3D(float(self.cartSat["x"]), float(self.cartSat["y"]),
            float(self.cartSat["z"]))
        velocity = Vector3D(float(self.cartSat["vx"]), float(self.cartSat["vy"]),
            float(self.cartSat["vz"]))

        celestialBody = CelestialBodyFactory.getBody(self.celestialBody)
        mu = CelestialBodyFactory.getBody(self.celestialBody).getGM()
        if self.celestialBody == 'EARTH':
            inertialFrame = FramesFactory.getEME2000()
        else:
            inertialFrame = celestialBody.getInertiallyOrientedFrame()

        orbit = KeplerianOrbit(PVCoordinates(position, velocity), inertialFrame,
            AbsoluteDate(self.startDate, TimeScalesFactory.getUTC()), mu)
        smaInit = orbit.getA()
        eccInit = orbit.getE()
        incInit = np.rad2deg(orbit.getI())
        raanInit = np.rad2deg(orbit.getRightAscensionOfAscendingNode())
        paInit = np.rad2deg(orbit.getPerigeeArgument())
        maInit = np.rad2deg(orbit.getMeanAnomaly())

        sma = CartSatKeplerian[:,2]*1e3 # in m
        ecc = CartSatKeplerian[:,3]
        inc = CartSatKeplerian[:,4]
        raan = CartSatKeplerian[:,5]
        raan[raan<-180] = raan[raan<-180]+360
        pa = CartSatKeplerian[:,6]
        pa[pa<-180] = pa[pa<-180]+360

        self.assertAlmostEqual(np.min(sma), np.max(sma), 3)
        self.assertAlmostEqual(np.mean(sma), smaInit, 3)

        self.assertAlmostEqual(np.min(ecc), np.max(ecc), 3)
        self.assertAlmostEqual(np.mean(ecc), eccInit, 3)

        self.assertAlmostEqual(np.min(inc), np.max(inc), 3)
        self.assertAlmostEqual(np.mean(inc), incInit, 3)

        self.assertAlmostEqual(np.min(raan), np.max(raan), 3)
        self.assertAlmostEqual(np.mean(raan), raanInit, 3)

        self.assertAlmostEqual(np.min(pa), np.max(pa), 3)
        self.assertAlmostEqual(np.mean(pa), paInit, 3)

        # Mean Anomaly
        # Compute times
        mjd = np.trunc(CartSatKeplerian[:,0])
        seconds = CartSatKeplerian[:,1]
        times = []
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        # Compute analytic mean anomalies, from SMA and central body's mu
        for i in range(len(mjd)):
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            dateTime = DateTimeComponents(date, time)
            times.append( dateTime.offsetFrom(dateTimeStart) )
        times = np.array(times)

        ma_analytic = np.rad2deg((mu/smaInit**3)**0.5)*times + maInit
        ma_analytic = np.mod(ma_analytic, 360)
        ma_analytic[ma_analytic>180] = ma_analytic[ma_analytic>180]-360

        ma = CartSatKeplerian[:,7]
        self.assertTrue(np.all(np.abs(ma - ma_analytic) < 1e-3))


if __name__ == '__main__':   
    unittest.main()
