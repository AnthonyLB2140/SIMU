from enum import Enum

# Keywords for CIC Mission Ephemeris Messages.
class PredefinedUserContent(Enum):
    # Latitude, Longitude, Altitude data
    LLA = ("LLA", "NONE", 3, "REAL", "[deg] [km]")

    # Keplerian data
    KEPLERIAN = ("KEPLERIAN", "NONE", 6, "REAL", "[deg] [km]")

    # Eclipse detection
    ECLIPSE = ("ECLIPSE", "NONE", 1, "STRING", "[n/a]")

    # Visibility station
    VISIBILITY = ("VISIBILITY", "NONE", 1, "STRING", "[n/a]")

    def __init__(self, nameType, protocol, dimension, typeCur, unit):
        self.nameType = nameType
        self.protocol = protocol
        self.dimension = dimension
        self.type = typeCur
        self.unit = unit

    @classmethod
    def getUserContent(cls, name):
        CODES_MAP = {}
        for typeData in cls:
            CODES_MAP[typeData.name] = typeData
        return CODES_MAP[name]
