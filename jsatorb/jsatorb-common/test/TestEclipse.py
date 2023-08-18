import orekit
vm = orekit.initVM()

from datetime import datetime
import traceback
import unittest
import sys
import os
import numpy as np

from org.hipparchus.util import FastMath

from org.orekit.bodies import OneAxisEllipsoid, CelestialBodyFactory
from org.orekit.frames import FramesFactory
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.events import EclipseDetector
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

class TestEclipse(unittest.TestCase):
    """
    Tests for generation of eclipse MEM files. This class tests if the files
    are correctly generated and if the data they contain are correct.
    """

    @classmethod
    def setUpClass(cls):
        """
        Generates Keplerian and Eclipse MEM files before tests with Earth
        as the central body, for two satellites, one defined with keplerian
        coordinates and the other one with cartesian coordinates
        The Keplerian MEM files are used to validate Eclipse MEM files.
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
        cls.utc = TimeScalesFactory.getUTC()

        options = {"KEPLERIAN":{}, "ECLIPSE":{}}
        fileGenerator = FileGenerator(cls.startDate, cls.endDate, cls.step,
            cls.celestialBody, cls.satellites, cls.groundStations, options)
        fileGenerator.generate(cls.dataFolder)

        if not os.path.isdir(cls.dataFolder):
            os.mkdir(cls.dataFolder)
        fileGenerator.generate(cls.dataFolder)

    def testEclipse(self):
        """
        Tests if the eclipse files have correctly been created
        """

        KepSatFileEclipse = self.dataFolder+'KepSat_MEM_ECLIPSE.TXT'
        CartSatFileEclipse = self.dataFolder+'CartSat_MEM_ECLIPSE.TXT'
        # Do files exist?
        self.assertTrue(os.path.exists(KepSatFileEclipse))
        self.assertTrue(os.path.exists(CartSatFileEclipse))
    
    def testEclipseKepSat(self):
        """
        Tests if the eclipse dates are correctly computed for the Keplerian
        satellite
        """

        KepSatFileEclipse = self.dataFolder+'KepSat_MEM_ECLIPSE.TXT'
        KepSatEclipse = np.genfromtxt(KepSatFileEclipse, skip_header=15)[:,:2]
        KepSatEclipseStates = np.genfromtxt(KepSatFileEclipse, delimiter=' ',
            skip_header=15, usecols=2, dtype=str)

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        sun = CelestialBodyFactory.getSun()
        sunRadius = ListCelestialBodies.getBody("SUN").radius
        
        eclipseDetector = EclipseDetector(sun, sunRadius, self.body)
        
        # Compute times
        mjd = np.trunc(KepSatKep[:,0])
        seconds = KepSatKep[:,1]
        listDates = []
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        listStates = []
        valueEclipseOld = 0
        # Compute LLA from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Find 0 of Eclipse Detector function to get events
            sma = float(KepSatKep[i,2])*1e3
            ecc = float(KepSatKep[i,3])
            inc = FastMath.toRadians(float(KepSatKep[i,4]))
            raan = FastMath.toRadians(float(KepSatKep[i,5]))
            pa = FastMath.toRadians(float(KepSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(KepSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            valueEclipse = eclipseDetector.g(SpacecraftState(currentOrbit))

            if valueEclipseOld < 0 and valueEclipse > 0:
                listDates.append(absoluteDate)
                listStates.append('DAY')
            elif valueEclipseOld > 0 and valueEclipse < 0:
                listDates.append(absoluteDate)
                listStates.append('NIGHT')

            valueEclipseOld = valueEclipse
        
        # Check if same number of events
        self.assertEqual(len(KepSatEclipse[:,0]), len(listStates))
        for i in range(len(KepSatEclipse[:,0])):
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH,
                int(KepSatEclipse[i,0]))
            time = TimeComponents(float(KepSatEclipse[i,1]))
            dateEclipseCur = AbsoluteDate(date, time, self.utc)

            # Check if same dates for events
            self.assertTrue(abs(dateEclipseCur.durationFrom(listDates[i])) < self.step)
            
            # Check if same types of events
            self.assertEqual(KepSatEclipseStates[i], listStates[i])

    def testEclipseCartSat(self):
        """
        Tests if the eclipse dates are correctly computed for the Cartesian
        satellite
        """

        CartSatFileEclipse = self.dataFolder+'CartSat_MEM_ECLIPSE.TXT'
        CartSatEclipse = np.genfromtxt(CartSatFileEclipse, skip_header=15)[:,:2]
        CartSatEclipseStates = np.genfromtxt(CartSatFileEclipse, delimiter=' ',
            skip_header=15, usecols=2, dtype=str)

        CartSatFileKep = self.dataFolder+'CartSat_MEM_KEPLERIAN.TXT'
        CartSatKep = np.genfromtxt(CartSatFileKep, skip_header=15)

        sun = CelestialBodyFactory.getSun()
        sunRadius = ListCelestialBodies.getBody("SUN").radius
        
        eclipseDetector = EclipseDetector(sun, sunRadius, self.body)
        
        # Compute times
        mjd = np.trunc(CartSatKep[:,0])
        seconds = CartSatKep[:,1]
        listDates = []
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)

        listStates = []
        valueEclipseOld = 0
        # Compute LLA from Kep coords
        for i in range(len(mjd)):
            # Get Date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)
            
            # Find 0 of Eclipse Detector function to get events
            sma = float(CartSatKep[i,2])*1e3
            ecc = float(CartSatKep[i,3])
            inc = FastMath.toRadians(float(CartSatKep[i,4]))
            raan = FastMath.toRadians(float(CartSatKep[i,5]))
            pa = FastMath.toRadians(float(CartSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(CartSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            valueEclipse = eclipseDetector.g(SpacecraftState(currentOrbit))

            if valueEclipseOld < 0 and valueEclipse > 0:
                listDates.append(absoluteDate)
                listStates.append('DAY')
            elif valueEclipseOld > 0 and valueEclipse < 0:
                listDates.append(absoluteDate)
                listStates.append('NIGHT')

            valueEclipseOld = valueEclipse
        
        # Check if same number of events
        self.assertEqual(len(CartSatEclipse[:,0]), len(listStates))
        for i in range(len(CartSatEclipse[:,0])):
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH,
                int(CartSatEclipse[i,0]))
            time = TimeComponents(float(CartSatEclipse[i,1]))
            dateEclipseCur = AbsoluteDate(date, time, self.utc)

            # Check if same dates for events
            self.assertTrue(abs(dateEclipseCur.durationFrom(listDates[i])) < self.step)
            
            # Check if same types of events
            self.assertEqual(CartSatEclipseStates[i], listStates[i])
        
if __name__ == '__main__':   
    unittest.main()
