import random

class WalkerConstellation:
    '''
    Class that generates a constellation according to the Walker Delta Pattern t:p:f, used in the GUI.
    The output is a python dictionary.
    t: number of satellites
    p: number of equally spaced planes
    f: relative spacing between satellites in adjacent planes
    '''

    def __init__(self, argConstellation):

        # Name
        self.name = str( argConstellation['name'])

        # Color
        if 'color' in argConstellation:
            self.color = argConstellation['color']
            self.uniqueColor = True
        else:
            self.uniqueColor = False

        # SMA or radius
        self.sma = float(argConstellation['sma'])

        # Inclination
        self.inc = float(argConstellation['inc'])

        # RAAN of first orbit
        self.firstraan = float(argConstellation['firstraan'])

        # Number of satellites
        self.t = int(argConstellation['t'])
        # Number of equally spaced planes
        self.p = int(argConstellation['p'])
        # Relative spacing between satellites in adjacent planes
        self.f = int(argConstellation['f'])

    def generate(self):
        satellites = []

        # Number of satellites per plane
        s = self.t/self.p
        if s.is_integer():
            s = int(s)
        else:
            raise(ValueError('Number of satellites per plane (t/p) should be integer'))

        for idxP in range(self.p):
            raan = self.firstraan + idxP*360./self.p
            for idxS in range(s):
                meanAnomaly = idxP*self.f*360./self.t + idxS*360./s

                nameSat = self.name + '_' + str(s*idxP + idxS)

                satCur = {}
                satCur['name'] = nameSat
                satCur['type'] = 'keplerian'

                # If specified color, set to this color
                # Otherwise, use a random hex color
                if self.uniqueColor:
                    satCur['color'] = self.color
                else:
                    red = "{:02x}".format(random.randint(0, 255))
                    green = "{:02x}".format(random.randint(0, 255))
                    blue = "{:02x}".format(random.randint(0, 255))
                    satCur['color'] = '#'+red+green+blue

                satCur['sma'] = self.sma
                satCur['ecc'] = 0.
                satCur['inc'] = self.inc
                satCur['pa'] = 0.
                satCur['raan'] = raan
                satCur['meanAnomaly'] = meanAnomaly

                satellites.append(satCur)

        return satellites

if __name__ == "__main__":
    # Example
    
    argConst = {
        'name': 'myConst',
        'sma': 7000000.,
        'inc': 15.,
        'firstraan': 10.,
        't': 9,
        'p': 3,
        'f': 1
    }
    walkerConst = WalkerConstellation(argConst)
    satellites = walkerConst.generate()
    for sat in satellites:
        print(sat['name'])
    for sat in satellites:
        print(sat['type'])
    for sat in satellites:
        print(sat['sma'])
    for sat in satellites:
        print(sat['ecc'])
    for sat in satellites:
        print(sat['inc'])
    for sat in satellites:
        print(sat['pa'])
    for sat in satellites:
        print(sat['raan'])
    for sat in satellites:
        print(sat['meanAnomaly'])
    
        