from enum import Enum, auto

# Keywords for CIC Mission Ephemeris Messages.
class MEMKeyword(Enum):

    # CIC MEM format version.
    CIC_MEM_VERS = auto()

    # Comments specific to MEM file.
    COMMENT = auto()

    # File creation date in UTC.
    CREATION_DATE = auto()

    # Creating agency or operator.
    ORIGINATOR = auto()

    # Spacecraft name for which the orbit state is provided.
    OBJECT_NAME = auto()

    # Object identifier of the object for which the orbit state is provided.
    OBJECT_ID = auto()

    # Time system used for data.
    TIME_SYSTEM = auto()

    # Name of the protocol used for the data (CIC or NONE).
    USER_DEFINED_PROTOCOL = auto()

    # Variable described by the data. Interpretation depends on the value
    # for USER_DEFINED_PROTOCOL.
    USER_DEFINED_CONTENT = auto()

    # Number of value fields in a data line, if the variable
    # described by the MEM file isn’t part of a protocol.
    USER_DEFINED_SIZE = auto()

    # Data type of the ephemerides, if the variable described by
    # the MEM file isn’t part of a protocol.  
    USER_DEFINED_TYPE = auto()

    # Unit for the ephemerides, if the variable described by
    # the MEM file isn’t part of a protocol.
    USER_DEFINED_UNIT = auto()
