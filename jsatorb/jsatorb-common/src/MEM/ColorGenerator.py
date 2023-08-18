import orekit
vm = orekit.initVM()

from collections import OrderedDict 
from datetime import datetime
from random import random

from org.orekit.time import AbsoluteDate, TimeScalesFactory

from MEMKeyword import MEMKeyword

class ColorGenerator:
    '''
    Class that generates the color files for VTS
    '''

    SPACE = ' '
    NEW_LINE = '\n'
    KV_FORMAT = "{} = {}\n"

    def __init__(self, stringDate, nameFile, satellite):
        self.timeScale = TimeScalesFactory.getUTC()
        self.initialDate = AbsoluteDate(stringDate, self.timeScale)
        self.nameFile = nameFile
        self.satellite = satellite
        if 'color' in satellite:
            guiColor = satellite['color']
            satColorR =  guiColor[1:3]
            satColorG =  guiColor[3:5]
            satColorB =  guiColor[5:]
            self.color = "{} {} {}".format(int(satColorR, 16)/255, int(satColorG, 16)/255, int(satColorB, 16)/255)
            # DEBUG TRACE print("CONVERTED COLOR, FROM " + guiColor + " -> " + self.color)
        else:
            self.color = "{} {} {}".format(random(), random(), random())
            # DEBUG TRACE print("RANDOM COLOR")

    # Write a single key and value to the stream using Key Value Notation (KVN).
    def writeKeyValue(self, writer, key, value):
        writer.write(self.KV_FORMAT.format(key.name, value))

    def generate(self):
        # Metadata init
        CIC_MEM_VERS = "1.0"
        originator  = "CS Group"
        objectName  = self.satellite["name"]
        objectID    = self.satellite["name"]
        contentName = "COLOR"
        protocol    = "NONE"
        dimension   = str(3)
        dataType    = "REAL"
        dataUnit    = "[n/a]"

        # Header metadata
        metadata = OrderedDict()
        metadata[MEMKeyword.CIC_MEM_VERS] = CIC_MEM_VERS
        metadata[MEMKeyword.CREATION_DATE] = datetime.now().isoformat()
        metadata[MEMKeyword.ORIGINATOR] = originator
        metadata[MEMKeyword.TIME_SYSTEM] = self.timeScale.getName()

        metadata[MEMKeyword.OBJECT_NAME] = objectName
        metadata[MEMKeyword.OBJECT_ID] = objectID

        # Metadata relative to values in file
        data = OrderedDict()
        data.update(metadata)
        data[MEMKeyword.USER_DEFINED_PROTOCOL] = protocol
        data[MEMKeyword.USER_DEFINED_CONTENT] = contentName
        data[MEMKeyword.USER_DEFINED_SIZE] = dimension
        data[MEMKeyword.USER_DEFINED_TYPE] = dataType
        data[MEMKeyword.USER_DEFINED_UNIT] = dataUnit

        with open(self.nameFile, 'w') as colorFile:
            self.writeKeyValue(colorFile, MEMKeyword.CIC_MEM_VERS,
                metadata[MEMKeyword.CIC_MEM_VERS])
            self.writeKeyValue(colorFile, MEMKeyword.CREATION_DATE,
                metadata[MEMKeyword.CREATION_DATE])
            self.writeKeyValue(colorFile, MEMKeyword.ORIGINATOR,
                metadata[MEMKeyword.ORIGINATOR])
            colorFile.write(self.NEW_LINE)

            colorFile.write("META_START")
            colorFile.write(self.NEW_LINE)

            # Section 4.3.2 - Mandatory keys
            self.writeKeyValue(colorFile, MEMKeyword.OBJECT_NAME, data[MEMKeyword.OBJECT_NAME])
            self.writeKeyValue(colorFile, MEMKeyword.OBJECT_ID, data[MEMKeyword.OBJECT_ID])
            self.writeKeyValue(colorFile, MEMKeyword.USER_DEFINED_PROTOCOL, data[MEMKeyword.USER_DEFINED_PROTOCOL])
            self.writeKeyValue(colorFile, MEMKeyword.USER_DEFINED_CONTENT, data[MEMKeyword.USER_DEFINED_CONTENT])

            # Section 4.3.2 - Optional keys
            if MEMKeyword.USER_DEFINED_SIZE in data:
                self.writeKeyValue(colorFile, MEMKeyword.USER_DEFINED_SIZE, str(data[MEMKeyword.USER_DEFINED_SIZE]))
            if MEMKeyword.USER_DEFINED_TYPE in data:
                self.writeKeyValue(colorFile, MEMKeyword.USER_DEFINED_TYPE, data[MEMKeyword.USER_DEFINED_TYPE])
            if MEMKeyword.USER_DEFINED_UNIT in data:
                self.writeKeyValue(colorFile, MEMKeyword.USER_DEFINED_UNIT, data[MEMKeyword.USER_DEFINED_UNIT])

            self.writeKeyValue(colorFile, MEMKeyword.TIME_SYSTEM, data[MEMKeyword.TIME_SYSTEM])

            # Stop metadata
            colorFile.write("META_STOP")
            colorFile.write(self.NEW_LINE)
            colorFile.write(self.NEW_LINE)

            # Data Color
            # Epoch
            epoch = self.dateToString(self.initialDate.getComponents(self.timeScale))
            colorFile.write(epoch)
            colorFile.write(self.SPACE)
            colorFile.write(self.color)
            colorFile.write(self.NEW_LINE)

    # Convert a date to a string
    @classmethod
    def dateToString(cls, components):
        date = components.getDate()
        time = components.getTime()
        mjd = date.getMJD()
        second = time.getSecondsInLocalDay()
        return str(mjd) + cls.SPACE + str(second)

    def addVisibilities(self, listNameFiles):
        '''
        Method that deals with the color changes due to visibility
        '''
        listTimes = []
        for nameFileCur in listNameFiles:
            with open(nameFileCur, 'r') as fileCur:
                for line in fileCur:
                    if ' START' in line or ' END' in line:
                        listTimes = self.sortDate(listTimes, line)
        with open(self.nameFile, 'a') as colorFile:
            for lineTime in listTimes:
                colorFile.write(lineTime.replace('START', '1 1 1').replace('END', self.color))

    @classmethod
    def sortDate(cls, listCur, line):
        '''
        Method that sort a list of dates, for visibility
        '''
        lineSplit = line.split(' ')
        day = int(lineSplit[0])
        seconds = float(lineSplit[1])
        for idx, lineCur in enumerate(listCur):
            lineCurSplit = lineCur.split(' ')
            dayCur = int(lineCurSplit[0])
            if day < dayCur:
                listCur.insert(idx, line)
                break
            elif day == dayCur:
                secondsCur = float(lineCurSplit[1])
                if seconds < secondsCur:
                    listCur.insert(idx, line)
                    break
        else:
            listCur.append(line)
        return listCur
        