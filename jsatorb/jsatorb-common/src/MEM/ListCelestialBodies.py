import orekit
vm = orekit.initVM()

from enum import Enum

from org.orekit.utils import Constants

class ListCelestialBodies(Enum):
    '''
    This Enum class contains equatorial radius and flattening data for all celestial
    bodies available in JSatOrb.
    Values are taken from https://nssdc.gsfc.nasa.gov/planetary/factsheet/*fact.html 
    where * represents the body's name.
    For the Earth, the considered values are the WGS84 ones.

    The different fields are: Celestial body : name, equatorial radius, flattening
    '''

    SUN = ("SUN", Constants.SUN_RADIUS, 0.00005)

    MERCURY = ("MERCURY", 2439.7e3, 0.)

    VENUS = ("VENUS", 6051.8e3, 0.)

    EARTH = ("EARTH", Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                Constants.WGS84_EARTH_FLATTENING)

    MARS = ("MARS", 3396.2e3, 0.00589)

    JUPITER = ("JUPITER", 71492e3, 0.06487)

    SATURN = ("SATURN", 60268e3, 0.09796)

    URANUS = ("URANUS", 25559e3, 0.02293)

    NEPTUNE = ("NEPTUNE", 24764e3, 0.01708)

    PLUTO = ("PLUTO", 1188e3, 0.)

    MOON = ("MOON", 1738.1e3, 0.0012)

    def __init__(self, nameBody, radius, flattening):
        self.nameBody = nameBody
        self.radius = radius
        self.flattening = flattening

    @classmethod
    def getBody(cls, name):
        CODES_MAP = {}
        for typeBody in cls:
            CODES_MAP[typeBody.name] = typeBody
        return CODES_MAP[name]