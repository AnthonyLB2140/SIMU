from datetime import  datetime

class Pass_object():

    def __init__(self, filename = None):

        if filename is not None:

            self.load_from_file(filename)

        else:

            self.t = []

            self.alt = []

            self.az = []

            self.len = 0

        self.satellite = ""

    def getStartDate(self):

        if self.len > 0:

            return self.t[0]

        else:

            return None

    def getStartAz(self):

        if self.len > 0:

            return self.az[0]

        else:

            return None

    def getStartAlt(self):

        if self.len > 0:

            return self.alt[0]

        else:

            return None

    def getEndDate(self):

        if self.len > 0:

            return self.t[-1]

        else:

            return None

    def getEndAz(self):

        if self.len > 0:

            return self.az[-1]

        else:

            return None

    def getEndAlt(self):

        if self.len > 0:

            return self.alt[-1]

        else:

            return None

    def append(self, t, alt, az):

        self.t.append(t)

        self.alt.append(alt)

        self.az.append(az)

        self.len += 1

    def save_to_file(self, filename):

        with open(filename, 'w') as f:

            for i in range(self.len):

                line = self.t[i].strftime('%Y, %m, %d, %H, %M, %S.%f, ')

                line += '%f, ' % self.alt[i]

                line += '%f\n' % self.az[i]

                f.write(line)

    def load_from_file(self, filename):

        self.t = []

        self.alt = []

        self.az = []

        self.len = 0

        with open(filename) as f:

            for line in f:

                splited = line.split(', ')

                year = int(splited[0])

                month = int(splited[1])

                day = int(splited[2])

                hour = int(splited[3])

                min = int(splited[4])

                sec = float(splited[5])

                alt = float(splited[6])

                az = float(splited[7])

                t = datetime(year=year, month=month, day=day, hour=hour, minute=min, second=int(sec), microsecond=int ((sec%1) * 1000000))

                self.append(t, alt, az)

    def getCulmination(self):

        return max(self.alt)

    def display(self):

        for i in range(self.len):

            print(self.t[i], self.alt[i], self.az[i])

    def __iter__(self):

        return ((self.t[i], self.alt[i], self.az[i]) for i in range(self.len))

if __name__ == "__main__":

    p = Pass_object()

    p.load_from_file('/home/c.lement/Documents/Lupin/Simu_station/git/lupin/src/pass_manager_orekit/2018_12_04_08h16_previsions_antenna_config/ISS/2018_12_04_13h37.csv')

    p.display()

    p.save_to_file('testestestest.csv')

    for pp in p:

        print(pp)