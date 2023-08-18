def parse_tle(line1, line2):
    keplerian = {}

    keplerian['mean_motion'] = float(line2[52:63])
    keplerian['eccentricity'] = float('0.' + line2[26:33])
    keplerian['inclination'] = float(line2[8:16])
    keplerian['right_ascension'] = float(line2[17:25])
    keplerian['argument_of_perigee'] = float(line2[34:42])
    keplerian['mean_anomaly'] = float(line2[43:51])

    return keplerian

# Example usage:
tle_line_1 = '1 25544U 98067A   21281.53070690  .00000238  00000+0  59288-4 0  9994'
tle_line_2 = '2 25544  51.6437 243.3392 0008446  38.9637 321.1813 15.48757739290498'

tle_parameters = parse_tle(tle_line_1, tle_line_2)
print(tle_parameters)

