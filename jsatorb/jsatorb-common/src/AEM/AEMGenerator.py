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
from math import radians, pi, degrees
from org.hipparchus.util import FastMath
from org.orekit.orbits import OrbitType
from org.orekit.propagation.numerical import NumericalPropagator
from org.hipparchus.ode.nonstiff import DormandPrince853Integrator
from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator
from org.orekit.forces.gravity.potential import GravityFieldFactory
from org.orekit.forces.gravity import HolmesFeatherstoneAttractionModel
from org.orekit.forces.gravity import NewtonianAttraction
from org.orekit.propagation import Propagator, SpacecraftState
def parse_tle(line1, line2):
    
    keplerian = {}
    
    keplerian['mean_motion'] = float(line2[52:63])
    keplerian['eccentricity'] = float('0.' + line2[26:33])
    keplerian['inclination'] = float(line2[8:16])
    keplerian['right_ascension'] = float(line2[17:25])
    keplerian['argument_of_perigee'] = float(line2[34:42])
    keplerian['mean_anomaly'] = float(line2[43:51])
        # Calculate semi-major axis (a) using mean motion (n) and Earth's gravitational constant (mu)
    mu = Constants.WGS84_EARTH_MU  # Earth's gravitational constant in km^3/s^2
    n = keplerian['mean_motion'] * 2 * FastMath.PI / 86400  # Convert mean motion to radians/minute
    a = (mu / (n ** 2)) ** (1 / 3)  # Calculate semi-major axis in kilometers
    keplerian['semi_major_axis'] = a
    
    
    return keplerian
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
####
            orbit = TLE(sat["line1"], sat["line2"])

            keplerian = parse_tle(sat["line1"], sat["line2"])          
            initialOrbit = KeplerianOrbit(keplerian['semi_major_axis'], keplerian['eccentricity'],
            radians(keplerian['inclination']), radians(keplerian['argument_of_perigee']),
            radians(keplerian['right_ascension']), radians(keplerian['mean_anomaly']),
            PositionAngle.MEAN, self.inertialFrame, orbit.getDate(), self.mu)
            #self.absoluteEndTime = self.absoluteStartTime.shiftedBy(self.duration)
            defaultMass = 2.0
            initialState = SpacecraftState(initialOrbit,defaultMass)
            integrator = ClassicalRungeKuttaIntegrator(self.timeStep)
            propagator = NumericalPropagator(integrator)
   
            gravityProvider = GravityFieldFactory.getNormalizedProvider(10, 10)
            propagator.addForceModel(HolmesFeatherstoneAttractionModel(FramesFactory.getITRF(IERSConventions.IERS_2010, True), gravityProvider))
            # propagator.addForceModel(NewtonianAttraction(self.mu))
            propagator.setInitialState(initialState)
            propagator.setOrbitType(initialOrbit.getType())
            print("Initial Position :", initialOrbit.getPVCoordinates())
            print("Initial Orbit :", initialOrbit)
####
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
