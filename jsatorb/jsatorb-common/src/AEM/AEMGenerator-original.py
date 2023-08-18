import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

from math import radians

import sys
sys.path.append('src/')
from ListCelestialBodies import ListCelestialBodies

from java.util import HashMap
from java.lang import StringBuffer
from org.hipparchus.geometry.euclidean.threed import Rotation, Vector3D
from org.orekit.attitudes import AttitudeProvider, BodyCenterPointing, LofOffset, NadirPointing
from org.orekit.bodies import CelestialBodyFactory, OneAxisEllipsoid
from org.orekit.files.ccsds import Keyword, StreamingAemWriter 
from org.orekit.frames import FramesFactory, LOFType
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.propagation.analytical import KeplerianPropagator
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import Constants, IERSConventions, PVCoordinates

def WarningSMA(satType, satOrbit, centralBody, mu):
    """
    Function that issues a simple warning if the satellite's SMA is smaller
    than the equatorial radius of the body.
    For a TLE, the considered distance is the one deducted from the mean
    motion.
    It does not necessarily means the orbit will intersect the body.
    """

    if satType == 'cartesian' or satType == 'keplerian':
        if satOrbit.getA() < centralBody.getEquatorialRadius():
            print("WARNING: semi-major axis smaller than Equatorial Radius!")
    elif satType == 'TLE':
        nCur = satOrbit.getMeanMotion() # in rad/s
        radiusCur = mu**(1./3.) / nCur**(2./3.)
        if radiusCur < centralBody.getEquatorialRadius():
            print("WARNING: initial semi-major axis smaller than Equatorial Radius!")


class AEMGenerator:
    """ Class that generates AEM Attitude files, using Orekit StreamingAemWriter """

    def __init__(self, stringDateStart, timeStep, stringDateEnd, bodyString):
        self.initialDate = AbsoluteDate(stringDateStart, TimeScalesFactory.getUTC())
        self.timeStep = timeStep
        self.endDate = AbsoluteDate(stringDateEnd, TimeScalesFactory.getUTC())

        celestialBody = CelestialBodyFactory.getBody(bodyString.upper())
        if bodyString.upper() == 'EARTH':
            bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
            self.inertialFrame = FramesFactory.getEME2000()
        else:
            bodyFrame = celestialBody.getBodyOrientedFrame()
            self.inertialFrame = celestialBody.getInertiallyOrientedFrame()
            #self.inertialFrame = FramesFactory.getEME2000()

        celestialBodyShape = ListCelestialBodies.getBody(bodyString.upper())
        radiusBody = celestialBodyShape.radius
        flatBody = celestialBodyShape.flattening
        self.body = OneAxisEllipsoid(radiusBody, flatBody, bodyFrame)
        self.mu = celestialBody.getGM()
            
        self.listFiles = []

    # Set satellite from JSON, and create orbit and propagator
    def setSatellite(self, sat):
        if(sat["type"] == "keplerian"):
            orbit = KeplerianOrbit(float(sat["sma"]), float(sat["ecc"]),
                radians(float(sat["inc"])), radians(float(sat["pa"])),
                radians(float(sat["raan"])), radians(float(sat["meanAnomaly"])),
                PositionAngle.MEAN, self.inertialFrame, self.initialDate, self.mu)

            self.satellite = {
                "name": sat["name"],
                "initialOrbit": orbit,
                "propagator": KeplerianPropagator(orbit)
            }

        elif(sat["type"] == "cartesian"):
            position = Vector3D(float(sat["x"]), float(sat["y"]), float(sat["z"]))
            velocity = Vector3D(float(sat["vx"]), float(sat["vy"]), float(sat["vz"]))
            orbit = KeplerianOrbit(PVCoordinates(position, velocity), self.inertialFrame,
                self.initialDate, self.mu)

            self.satellite = {
                "name": sat["name"],
                "initialOrbit": orbit,
                "propagator": KeplerianPropagator(orbit)
            }

        elif(sat["type"] == "tle"):
            line1 = sat["line1"]
            line2 = sat["line2"]
            orbit = TLE(line1, line2)
            propagator = TLEPropagator.selectExtrapolator(orbit)
            self.initialDate = orbit.getDate()

            self.satellite = {
                "name": sat["name"],
                "initialOrbit": orbit,
                "propagator": propagator
            }

        else:
            raise TypeError("Unknown satellite type")

        # Check if satellite outside central body
        WarningSMA(sat["type"], orbit, self.body, self.mu)

    def setFile(self, nameFile):
        self.nameFile = nameFile

        # Metadata init
        originator  = "CS Group"
        objectName  = self.satellite["name"]
        objectID    = self.satellite["name"]

        # Header data
        metadata = HashMap()
        metadata.put(Keyword.ORIGINATOR, originator)
        metadata.put(Keyword.OBJECT_NAME, objectName)
        metadata.put(Keyword.OBJECT_ID,   objectID)

        # Metadata relative to values in file
        segmentData = HashMap()
        segmentData.put(Keyword.OBJECT_NAME, objectName)
        segmentData.put(Keyword.ATTITUDE_DIR, "A2B")
        segmentData.put(Keyword.QUATERNION_TYPE, "LAST")
        segmentData.put(Keyword.ATTITUDE_TYPE, "QUATERNION")
        segmentData.put(Keyword.REF_FRAME_A, "EME2000")
        segmentData.put(Keyword.REF_FRAME_B, "SC_BODY_1")

        self.buffer = StringBuffer()
        writer = StreamingAemWriter(self.buffer, TimeScalesFactory.getUTC(), metadata)
        writer.writeHeader()

        segment = writer.newSegment(segmentData)
        self.satellite["propagator"].setMasterMode(self.timeStep, segment)

    def setAttitudeLaw(self, optionsAttitude):
        if 'law' in optionsAttitude:
            lawAttitudeStr = optionsAttitude['law']
        else:
            print('No attitude chosen')
            lawAttitudeStr = 'LOF_VVLH'

        inertialFrame = self.satellite["propagator"].getFrame()

        if 'LOF' in lawAttitudeStr:
            lofType = LOFType.valueOf(lawAttitudeStr.split('LOF_')[1])
            attitudeLaw = LofOffset(inertialFrame, lofType)
        elif lawAttitudeStr == 'NADIR':
            attitudeLaw = NadirPointing(inertialFrame, self.body)
        elif 'POINTING' in lawAttitudeStr:
            if 'CENTRAL' in lawAttitudeStr:
                bodyTarget = self.body
            elif 'SUN' in lawAttitudeStr:
                sunShape = ListCelestialBodies.getBody('SUN')
                sunBody = CelestialBodyFactory.getBody('SUN')
                bodyTarget = OneAxisEllipsoid(sunShape.radius, 
                    sunShape.flattening, sunBody.getBodyOrientedFrame())
            attitudeLaw = BodyCenterPointing(inertialFrame, bodyTarget)
        else:
            raise NameError("Unknown attitude law")

        self.satellite["propagator"].setAttitudeProvider(attitudeLaw)

    def propagate(self):
        self.satellite["propagator"].propagate(self.endDate)
        with open(self.nameFile, 'w') as file:
            file.write(self.buffer.toString())

    
if __name__ == "__main__":
    mySatelliteKeplerian = {
        "name": "Lucien-Sat",
        "type": "keplerian",
        "sma": 7000000,
        "ecc": 0.007014455530245822,
        "inc": 51,
        "pa": 0,
        "raan": 0,
        "meanAnomaly": 0,
    }

    mySatelliteCartesian = {
        "name": "Thibault-Sat",
        "type": "cartesian",
        "x": -6142438.668,
        "y": 3492467.560,
        "z": -25767.25680,
        "vx": 505.8479685,
        "vy": 942.7809215,
        "vz": 7435.922231,
    }

    mySatelliteTLE = {
        "name": "ISS (ZARYA)",
        "type": "tle",
        "line1": "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927",
        "line2": "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
    }

    step = 10.0
    stringDateStart = "2020-03-03T14:42:28.6Z"
    stringDateEnd = "2020-03-02T14:42:28.6Z"
    bodyString = 'EARTH'

    aemGenerator = AEMGenerator(stringDateStart, step, stringDateEnd,bodyString)
    aemGenerator.setSatellite(mySatelliteKeplerian)
    aemGenerator.setFile('exampleKep.AEM')
    aemGenerator.setAttitudeLaw({'law': 'NADIR'})
    aemGenerator.propagate()
