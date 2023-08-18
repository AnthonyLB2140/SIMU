import orekit
vm = orekit.initVM()

from datetime import datetime
import traceback
import unittest
import sys
import os
import numpy as np

from org.hipparchus.geometry.euclidean.threed import Rotation, Vector3D
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

class TestAttitude(unittest.TestCase):
    """
    Tests for generation of attitude files. This class tests if the files are
    correctly generated and if the data they contain are correct. Most examples
    deal with Earth but there is also a test for Mars, since AEM CIC files require
    an additional rotation for non-Earth bodies in order to use EME2000 axes.
    """

    @classmethod
    def setUpClass(cls):
        """
        Generates Keplerian MEM and Attitude AEM files before tests
        with Earth as the central body
        The Keplerian MEM files are used to validate AEM files.
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

        options = {"KEPLERIAN":{}, "ATTITUDE":{}}
        fileGenerator = FileGenerator(cls.startDate, cls.endDate, cls.step,
            cls.celestialBody, cls.satellites, cls.groundStations, options)

        # Generates files in the files folder
        if not os.path.isdir(cls.dataFolder):
            os.mkdir(cls.dataFolder)
        fileGenerator.generate(cls.dataFolder)

    def testAttitude(self):
        """
        Tests if the attitude file has correctly been created
        """
        KepSatFileAtt = self.dataFolder+'KepSat_AEM_ATTITUDE.TXT'

        # Does file exist?
        self.assertTrue(os.path.exists(KepSatFileAtt))

    def testAttitudeDates(self): 
        """
        Tests if the start and end dates in the attitude data file are right
        """ 
        KepSatFileAtt = self.dataFolder+'KepSat_AEM_ATTITUDE.TXT'
        KepSatAtt = np.genfromtxt(KepSatFileAtt, skip_header=18)

        # Does it begin and end at right dates?
        mjd = int(np.trunc(KepSatAtt[0,0]))
        seconds = float(KepSatAtt[0,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeStart = DateTimeComponents.parseDateTime(self.startDate)
        self.assertTrue(dateTime.equals(dateTimeStart))

        mjd = int(np.trunc(KepSatAtt[-1,0]))
        seconds = float(KepSatAtt[-1,1])
        date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, mjd)
        time = TimeComponents(seconds)
        dateTime = DateTimeComponents(date, time)
        dateTimeEnd = DateTimeComponents.parseDateTime(self.endDate)
        self.assertTrue(dateTime.equals(dateTimeEnd))
    
    def testAttitudeCentralBody(self):
        """
        Tests if attitude is really pointing towards central body
        """
        options = {"ATTITUDE":{'law': 'POINTING_CENTRAL'}}
        fileGenerator = FileGenerator(self.startDate, self.endDate, self.step,
            self.celestialBody, self.satellites, self.groundStations, options)
        fileGenerator.generate(self.dataFolder)

        KepSatFileAtt = self.dataFolder+'KepSat_AEM_ATTITUDE.TXT'
        KepSatAtt = np.genfromtxt(KepSatFileAtt, skip_header=18)

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        # Test if files have same length
        self.assertTrue(len(KepSatKep[:,0]) == len(KepSatAtt[:,0]))

        # Compute times
        mjd = np.trunc(KepSatAtt[:,0])
        seconds = KepSatAtt[:,1]

        # Compute angle Earth-Satellite and Satellite Z axis
        for i in range(len(mjd)):
            # Get date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)

            # Get Earth-Satellite vector
            sma = float(KepSatKep[i,2])*1e3
            ecc = float(KepSatKep[i,3])
            inc = FastMath.toRadians(float(KepSatKep[i,4]))
            raan = FastMath.toRadians(float(KepSatKep[i,5]))
            pa = FastMath.toRadians(float(KepSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(KepSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            currentPosition = currentOrbit.getPVCoordinates().getPosition()
            satEarthVector = currentPosition.negate()

            # Get Z Axis of satellite in inertial frame
            q0 = float(KepSatAtt[i,2])
            q1 = float(KepSatAtt[i,3])
            q2 = float(KepSatAtt[i,4])
            qc = float(KepSatAtt[i,5]) # Scalar

            rotationToEME2000 = Rotation(qc, q0, q1, q2, False).revert()
            satZAxis = rotationToEME2000.applyTo(Vector3D.PLUS_K)
            angleEarthPointing = FastMath.toDegrees(Vector3D.angle(satZAxis,
                satEarthVector))
            self.assertAlmostEqual(angleEarthPointing, 0., 3)
    
    def testAttitudeNadir(self):
        """
        Tests if attitude is really pointing towards nadir (local vertical)
        """
        options = {"ATTITUDE":{'law': 'NADIR'}}
        fileGenerator = FileGenerator(self.startDate, self.endDate, self.step,
            self.celestialBody, self.satellites, self.groundStations, options)
        fileGenerator.generate(self.dataFolder)

        KepSatFileAtt = self.dataFolder+'KepSat_AEM_ATTITUDE.TXT'
        KepSatAtt = np.genfromtxt(KepSatFileAtt, skip_header=18)

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        # Test if files have same length
        self.assertTrue(len(KepSatKep[:,0]) == len(KepSatAtt[:,0]))

        # Compute times
        mjd = np.trunc(KepSatAtt[:,0])
        seconds = KepSatAtt[:,1]

        # Compute surface normal vector and Satellite Z axis
        for i in range(len(mjd)):
            # Get date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)

            # Get Earth normal vector for geodetic coordinates
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

            latCur = point.getLatitude() # in rad
            longCur = point.getLongitude() # in rad
            
            xVert = FastMath.cos(longCur)*FastMath.cos(latCur)
            yVert = FastMath.sin(longCur)*FastMath.cos(latCur)
            zVert = FastMath.sin(latCur)
            targetVertical = Vector3D(xVert, yVert, zVert)

            # Get Z Axis of satellite in inertial frame
            q0 = float(KepSatAtt[i,2])
            q1 = float(KepSatAtt[i,3])
            q2 = float(KepSatAtt[i,4])
            qc = float(KepSatAtt[i,5]) # Scalar            

            rotationToEME2000 = Rotation(qc, q0, q1, q2, False).revert()
            satZAxisEME2000 = rotationToEME2000.applyTo(Vector3D.PLUS_K)
            transformInertialToBody = self.inertialFrame.getTransformTo(
                self.body.getBodyFrame(), absoluteDate)
            satZAxisBody = transformInertialToBody.transformVector(satZAxisEME2000)
            angleNadirPointing = FastMath.toDegrees(Vector3D.angle(satZAxisBody,
                targetVertical.negate()))
            self.assertAlmostEqual(angleNadirPointing, 0., 3)

    def testAttitudeLVLH(self):
        """
        Tests if attitude is really representing LVLH 
        """
        options = {"ATTITUDE":{'law': 'LOF_LVLH'}}
        fileGenerator = FileGenerator(self.startDate, self.endDate, self.step,
            self.celestialBody, self.satellites, self.groundStations, options)
        fileGenerator.generate(self.dataFolder)

        KepSatFileAtt = self.dataFolder+'KepSat_AEM_ATTITUDE.TXT'
        KepSatAtt = np.genfromtxt(KepSatFileAtt, skip_header=18)

        KepSatFileKep = self.dataFolder+'KepSat_MEM_KEPLERIAN.TXT'
        KepSatKep = np.genfromtxt(KepSatFileKep, skip_header=15)

        # Test if files have same length
        self.assertTrue(len(KepSatKep[:,0]) == len(KepSatAtt[:,0]))

        # Compute times
        mjd = np.trunc(KepSatAtt[:,0])
        seconds = KepSatAtt[:,1]

        # Compute angle Earth-Satellite, orbital momentum
        # and Satellite X and Z axes
        for i in range(len(mjd)):
            # Get date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)

            # Get Earth-Satellite vector
            sma = float(KepSatKep[i,2])*1e3
            ecc = float(KepSatKep[i,3])
            inc = FastMath.toRadians(float(KepSatKep[i,4]))
            raan = FastMath.toRadians(float(KepSatKep[i,5]))
            pa = FastMath.toRadians(float(KepSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(KepSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, self.inertialFrame, absoluteDate, self.mu)
            earthSatVector = currentOrbit.getPVCoordinates().getPosition()

            velocityVector = currentOrbit.getPVCoordinates().getVelocity()
            orbitalMomentumVector = earthSatVector.crossProduct(velocityVector)

            # Get X and Z Axes of satellite in inertial frame
            q0 = float(KepSatAtt[i,2])
            q1 = float(KepSatAtt[i,3])
            q2 = float(KepSatAtt[i,4])
            qc = float(KepSatAtt[i,5]) # Scalar

            rotationToEME2000 = Rotation(qc, q0, q1, q2, False).revert()
            satXAxis = rotationToEME2000.applyTo(Vector3D.PLUS_I)
            satZAxis = rotationToEME2000.applyTo(Vector3D.PLUS_K)

            angleXAxisPointing = FastMath.toDegrees(Vector3D.angle(satXAxis,
                earthSatVector))
            self.assertAlmostEqual(angleXAxisPointing, 0., 3)
            angleZAxisPointing = FastMath.toDegrees(Vector3D.angle(satZAxis,
                orbitalMomentumVector))
            self.assertAlmostEqual(angleZAxisPointing, 0., 3)

    def testAttitudeMars(self):
        """
        Tests if attitude is really pointing towards central body if central
        body is Mars
        """
        
        satellites = [
            {"name": "MarsSat",
            "type": "keplerian",
            "sma": 5000000,
            "ecc": 0.01,
            "inc": 10,
            "pa": 20,
            "raan": 15,
            "meanAnomaly": 10
            },
        ]
        groundStations = []
        celestialBody = 'MARS'

        inertialFrameEME2000 = FramesFactory.getEME2000()
        
        mars = CelestialBodyFactory.getMars()
        bodyFrameMars = mars.getBodyOrientedFrame()
        inertialFrameMars = mars.getInertiallyOrientedFrame()
        muMars = mars.getGM()
        
        # Generates new file with Mars as central body
        options = {"KEPLERIAN":{}, "ATTITUDE":{'law': 'POINTING_CENTRAL'}}
        fileGenerator = FileGenerator(self.startDate, self.endDate, self.step,
            celestialBody, satellites, groundStations, options)
        fileGenerator.generate(self.dataFolder)

        MarsSatFileAtt = self.dataFolder+'MarsSat_AEM_ATTITUDE.TXT'
        MarsSatAtt = np.genfromtxt(MarsSatFileAtt, skip_header=18)

        MarsSatFileKep = self.dataFolder+'MarsSat_MEM_KEPLERIAN.TXT'
        MarsSatKep = np.genfromtxt(MarsSatFileKep, skip_header=15)

        # Test if files have same length
        self.assertTrue(len(MarsSatKep[:,0]) == len(MarsSatAtt[:,0]))

        # Compute times
        mjd = np.trunc(MarsSatAtt[:,0])
        seconds = MarsSatAtt[:,1]

        # Compute angle Earth-Satellite and Satellite Z axis
        for i in range(len(mjd)):
            # Get date
            date = DateComponents(DateComponents.MODIFIED_JULIAN_EPOCH, int(mjd[i]))
            time = TimeComponents(float(seconds[i]))
            absoluteDate = AbsoluteDate(date, time, self.utc)

            # Get Mars-Satellite vector
            sma = float(MarsSatKep[i,2])*1e3
            ecc = float(MarsSatKep[i,3])
            inc = FastMath.toRadians(float(MarsSatKep[i,4]))
            raan = FastMath.toRadians(float(MarsSatKep[i,5]))
            pa = FastMath.toRadians(float(MarsSatKep[i,6]))
            meanAnomaly = FastMath.toRadians(float(MarsSatKep[i,7]))
            
            currentOrbit = KeplerianOrbit(sma, ecc, inc, pa, raan, meanAnomaly,
                PositionAngle.MEAN, inertialFrameMars, absoluteDate, muMars)
            currentPosition = currentOrbit.getPVCoordinates().getPosition()
            vectorSatMarsInertialMars = currentPosition.negate()
            transformMarsEME = inertialFrameMars.getTransformTo(inertialFrameEME2000,
                absoluteDate)
            rotationMarsEME = transformMarsEME.getRotation() 
            vectorSatMarsEME2000 = rotationMarsEME.applyTo(vectorSatMarsInertialMars)

            # Get Z Axis of satellite in inertial frame
            q0 = float(MarsSatAtt[i,2])
            q1 = float(MarsSatAtt[i,3])
            q2 = float(MarsSatAtt[i,4])
            qc = float(MarsSatAtt[i,5]) # Scalar

            rotationSatEME = Rotation(qc, q0, q1, q2, False).revert()
            satZAxisEME = rotationSatEME.applyTo(Vector3D.PLUS_K)
            angleMarsPointing = FastMath.toDegrees(Vector3D.angle(satZAxisEME,
                vectorSatMarsEME2000))
            self.assertAlmostEqual(angleMarsPointing, 0., 3)
            
   
if __name__ == '__main__':   
    unittest.main()
