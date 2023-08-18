import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

from org.hipparchus.geometry.euclidean.threed import Vector3D

from org.orekit.bodies import CelestialBodyFactory
from org.orekit.frames import FramesFactory
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.time import AbsoluteDate, TimeScalesFactory

from math import radians

'''
Function to convert coordinates around a non-Earth body from EME2000 axes to 
Orekit inertial frame associated with the body
It is currently not used in JSatOrb through the GUI, but can be used by users to transform
EME2000 coordinates to Orekit inertial frame associated to non-Earth bodies.
'''
def conversionEMEBody(stringBody, stringDate, sat):
    if stringBody.upper() != 'EARTH':
        centralBody = CelestialBodyFactory.getBody(stringBody.upper())
        inertialFrameBody = centralBody.getInertiallyOrientedFrame()
        inertialFrameEarth = FramesFactory.getEME2000()
        mu = centralBody.getGM()
           
        utc = TimeScalesFactory.getUTC()
        initialDate = AbsoluteDate(stringDate, utc)

        transformEMEBody = inertialFrameEarth.getTransformTo(inertialFrameBody, initialDate)
        rotationEMEBody = transformEMEBody.getRotation()

        if sat["type"] == "keplerian":
            orbit = KeplerianOrbit(float(sat["sma"]), float(sat["ecc"]),
                radians(float(sat["inc"])), radians(float(sat["pa"])),
                radians(float(sat["raan"])), radians(float(sat["meanAnomaly"])),
                PositionAngle.MEAN, inertialFrameEarth, initialDate, mu)
            position = orbit.getPVCoordinates().getPosition()
            velocity = orbit.getPVCoordinates().getVelocity()
        elif sat["type"] == "cartesian":
            position = Vector3D(float(sat["x"]), float(sat["y"]), float(sat["z"]))
            velocity = Vector3D(float(sat["vx"]), float(sat["vy"]), float(sat["vz"]))
        
        newSat = {}
        newSat["name"] = sat["name"]
        if "color" in sat:
            newSat["color"] = sat["color"]
        newSat["type"] = "cartesian"
        
        newPosition = rotationEMEBody.applyTo(position)
        newVelocity = rotationEMEBody.applyTo(velocity)
        newSat["x"] = newPosition.getX()
        newSat["y"] = newPosition.getY()
        newSat["z"] = newPosition.getZ()
        newSat["vx"] = newVelocity.getX()
        newSat["vy"] = newVelocity.getY()
        newSat["vz"] = newVelocity.getZ()
        
    else:
        newSat = sat

    return newSat

if __name__ == '__main__':
    body = 'MARS'
    date = "2011-12-01T16:43:45"
    satKep = {
        "name": "MarsSatKep",
        "type": "keplerian",
        "sma": 6000000,
        "ecc": 0.01,
        "inc": 51,
        "pa": 20,
        "raan": 15,
        "meanAnomaly": 10
    }
    satCart = {
        "name": "MarsSatCart",
        "type": "cartesian",
        "x": -6142438.668,
        "y": 3492467.560,
        "z": -25767.25680,
        "vx": 505.8479685,
        "vy": 942.7809215,
        "vz": 7435.922231
    }

    print(conversionEMEBody(body, date, satKep))
    print(conversionEMEBody(body, date, satCart))