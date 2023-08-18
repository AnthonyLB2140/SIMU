import orekit
vm = orekit.initVM()

from org.orekit.time import DateTimeComponents, DateComponents, TimeComponents
# from org.orekit.time import TimeScalesFactory, AbsoluteDate

class HAL_DateConversion:
    '''
    Class that performs the date conversion using orekit methods
    '''

    def __init__(self, dateToConvert, targetFormat):
        #self.utc = TimeScalesFactory.getUTC()
        #self.dateToConvert = AbsoluteDate(dateToConvert, self.utc)
        self.dateToConvert = dateToConvert
        self.targetFormat = targetFormat

    def getDateTime(self):
        '''
        Read the target format, get date and time depending on the wanted format
        Return converted date
        '''
        # Parse a string in ISO-8601 format
        dateTime = DateTimeComponents.parseDateTime(self.dateToConvert)
        date = dateTime.getDate()

        if self.targetFormat == 'JD':
            dateConverted = float(date.getMJD()) + 2400000.5
        elif self.targetFormat == 'MJD':
            dateConverted = float(date.getMJD())
        else:
            raise NameError("unknown target format")

        time = dateTime.getTime()
        fractionHour = time.getHour() / 24.
        fractionMinute = time.getMinute() / 60. / 24.
        fractionSecond = time.getSecond() / 3600. / 24.

        dateConvertedString = str( dateConverted + fractionHour + fractionMinute + fractionSecond )
        
        return { "dateConverted": dateConvertedString }





        
