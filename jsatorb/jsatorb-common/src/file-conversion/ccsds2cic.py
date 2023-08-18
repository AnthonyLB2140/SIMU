import orekit
vm = orekit.initVM()

from org.hipparchus.geometry.euclidean.threed import Rotation, Vector3D, RotationConvention

from org.orekit.bodies import CelestialBodyFactory
from org.orekit.frames import FramesFactory
from org.orekit.time import DateTimeComponents, DateComponents, TimeComponents
from org.orekit.time import AbsoluteDate, TimeScalesFactory


def dateValidation(dateString):
    try:
        dateTime = DateTimeComponents.parseDateTime(dateString)
        isDate = True
    except Exception:
        isDate = False
    return isDate

def ccsds2cic(nameFileIn, nameFileOut, stringBody):
    """ Convert CCSDS files into CIC files that can be read by VTS. 

    VTS requires Cartesian coordinates and Attitudes in an inertial frame
    whose center is the central body's center and the axes are the EME2000 axes.
    Therefore, for non-Earth bodies, this routine provides a rotation from
    the inertial frame associated with the body in Orekit to the EME2000 axes.
    """

    SPACE = ' '
    # If not Earth, rotation needed to consider EME2000 axes
    if stringBody.upper() != 'EARTH':
        rotationNeeded = True
        centralBody = CelestialBodyFactory.getBody(stringBody.upper())
        inertialFrameBody = centralBody.getInertiallyOrientedFrame()
        inertialFrameEarth = FramesFactory.getEME2000()
        utc = TimeScalesFactory.getUTC()
    else:
        rotationNeeded = False

    with open(nameFileOut, 'w') as fileOut, open(nameFileIn, 'r') as fileIn:
        for line in fileIn:
            if len(line) > 1:
                lineSplit = line.split()
                if line.startswith('CCSDS'):
                    if 'AEM' in line:
                        fileType = 'AEM'
                    elif 'OEM' in line:
                        fileType = 'OEM'
                    newLine = 'CIC' + line[5:]
                elif dateValidation(lineSplit[0]):
                    dateTime = DateTimeComponents.parseDateTime(lineSplit[0])
                    date = dateTime.getDate()
                    time = dateTime.getTime()
                    mjd = date.getMJD()
                    second = time.getSecondsInLocalDay()
                    lineSplit[0] = str(mjd) + SPACE + str(second)

                    if rotationNeeded:
                        transform = inertialFrameBody.getTransformTo(inertialFrameEarth,
                            AbsoluteDate(date, time, utc))
                        rotationBodyEME = transform.getRotation()                      

                    # Conversion of position and speed in kilometers and change of frame
                    # if not Earth
                    if fileType == 'OEM':
                        if rotationNeeded:
                            position = Vector3D(float(lineSplit[1]), float(lineSplit[2]),
                                float(lineSplit[3]))
                            newPosition = rotationBodyEME.applyTo(position)
                            lineSplit[1] = newPosition.getX()
                            lineSplit[2] = newPosition.getY()
                            lineSplit[3] = newPosition.getZ()

                            speed = Vector3D(float(lineSplit[4]), float(lineSplit[5]),
                                float(lineSplit[6]))
                            newSpeed = rotationBodyEME.applyTo(speed)
                            lineSplit[4] = newSpeed.getX()
                            lineSplit[5] = newSpeed.getY()
                            lineSplit[6] = newSpeed.getZ()

                        lineSplit[1:] = [str(float(coord)*1e-3) for coord in lineSplit[1:]]
                    
                    elif fileType == 'AEM' and rotationNeeded:
                        q0 = float(lineSplit[1])
                        q1 = float(lineSplit[2])
                        q2 = float(lineSplit[3])
                        qc = float(lineSplit[4])
                        rotationBodySat = Rotation(qc, q0, q1, q2, False)
                        rotationEMEBody = rotationBodyEME.revert()
                        rotationEMESat = rotationEMEBody.compose(rotationBodySat, RotationConvention.FRAME_TRANSFORM)
                        
                        qc = rotationEMESat.getQ0()
                        q0 = rotationEMESat.getQ1()
                        q1 = rotationEMESat.getQ2()
                        q2 = rotationEMESat.getQ3()
                        lineSplit[1] = str(q0)
                        lineSplit[2] = str(q1)
                        lineSplit[3] = str(q2)
                        lineSplit[4] = str(qc)
                    
                    newLine = ' '.join(lineSplit) + '\n'
                else:
                    newLine = line
            
            else:
                newLine = line
            fileOut.write(newLine)

if __name__ == '__main__':
    fileInOEM = 'file-conversion/test.OEM'
    fileOutOEM = 'converted.OEM'
    ccsds2cic(fileInOEM, fileOutOEM)

    fileInAEM = 'exampleKep.AEM'
    fileOutAEM = 'exampleKepCIC.AEM'
    ccsds2cic(fileInAEM, fileOutAEM)
