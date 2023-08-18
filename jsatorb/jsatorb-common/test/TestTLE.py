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
from org.orekit.propagation.analytical.tle import TLE
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

class TestTLE(unittest.TestCase):
    """
    Test that checks if the chosen starting date when a TLE is considered
    is the right one, i.e., if the TLE date is posterior to the given starting
    date, the TLE date is chosen as the actual starting date.
    """

    @classmethod
    def setUpClass(cls):
        """
        Generates Keplerian MEM files for satellites defined from a TLE and
        Keplerian coordinates
        """

        header = {
            "mission": "validation",
            "celestialBody": "EARTH",
            "timeStart": "2008-07-01T13:35:00",
            "timeEnd": "2008-09-23T15:15:00",
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
            {"name": "TLESat",
            "type": "tle",
            "line1": "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927",
            "line2": "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
            }
        ]
        cls.groundStations = []

        cls.step = float( header['step'] )
        cls.startDate = str( header['timeStart'] )
        cls.endDate = str( header['timeEnd'] )
        cls.celestialBody = str( header['celestialBody'] )
        cls.dataFolder = 'test/files/'
        cls.utc = TimeScalesFactory.getUTC()

        cls.mu = CelestialBodyFactory.getBody(cls.celestialBody).getGM()

        cls.kepSat = cls.satellites[0]
        cls.tleSat = cls.satellites[1]

        options = {"KEPLERIAN":{}}
        fileGenerator = FileGenerator(cls.startDate, cls.endDate, cls.step,
            cls.celestialBody, cls.satellites, cls.groundStations, options)
            
        if not os.path.isdir(cls.dataFolder):
            os.mkdir(cls.dataFolder)
        fileGenerator.generate(cls.dataFolder)

    def testTLEFiles(self):       
        """
        Tests if the files have correctly been created
        """

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        TLESatFileKep = self.dataFolder+'TLESat_MEM_KEPLERIAN.TXT'
        # Do files exist?
        self.assertTrue(os.path.exists(KepSatFileKep))
        self.assertTrue(os.path.exists(TLESatFileKep))

    def testTLEDates(self):
        """
        Tests if the starting date is correctly chosen, i.e., if it is the 
        TLE date when prior to given starting date
        """

        dateStartHeader = AbsoluteDate(self.startDate,self.utc)

        tleSatellite = TLE(self.tleSat["line1"], self.tleSat["line2"])
        dateStartTLE = tleSatellite.getDate()

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        TLESatFileKep = self.dataFolder+'TLESat_MEM_KEPLERIAN.TXT'
        TLESatKep = np.genfromtxt(TLESatFileKep, skip_header=15)

        # Start date for Keplerian file for KepSat
        mjdStart = np.trunc(KepSatKep[0,0])
        secondsStart = KepSatKep[0,1]
        dateStart = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjdStart))
        timeStart = TimeComponents(float(secondsStart))
        absoluteDateStart = AbsoluteDate(dateStart, timeStart, self.utc)
        self.assertAlmostEqual(absoluteDateStart.durationFrom(dateStartTLE), 0, 3)

        # Start date for Keplerian file for TLESat
        mjdStart = np.trunc(TLESatKep[0,0])
        secondsStart = TLESatKep[0,1]
        dateStart = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjdStart))
        timeStart = TimeComponents(float(secondsStart))
        absoluteDateStart = AbsoluteDate(dateStart, timeStart, self.utc)
        self.assertAlmostEqual(absoluteDateStart.durationFrom(dateStartTLE), 0, 3)

if __name__ == '__main__':   
    unittest.main()
