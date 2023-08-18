import orekit
vm = orekit.initVM()

from org.orekit.time import AbsoluteDate, TimeStamped

class TimeStampedMEMData(TimeStamped):

    '''
    Build a new instance.
    AbsoluteDate epoch: date of the data
    String data: data present in the MEM data line
    '''
    def __init__(self, epoch, data):
        self.epoch = epoch
        self.data = data
