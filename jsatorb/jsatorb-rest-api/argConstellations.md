# List of arguments for a constellation
This is the list of arguments that can be taken for the generation of a constellation.

## 'name'
Name of the whole constellation. Names of the satellites will be name1, name2, ...

## 'color'
Optional, depends if we want a unique color for the whole constellation or not.
If no color, each satellite has its own color.

## 'sma'
Semi-major axis (which is also the radius since we consider no eccentricity (in m).

## 'inc'
Inclination of the planes (in deg).

## 'firstraan'
RAAN of the first orbit plane

## 't'
First of the Walker Delta Pattern parameters :
Total number of satellites

## 'p'
Second of the Walker Delta Pattern parameters :
Number of equally spaced planes

## 'f'
Third of the Walker Delta Pattern parameters :
Relative spacing between satellites in adjacent planes

A change in true anomaly in degreees for equivalent satellites in neighbouring planes is
equal to the phase difference f*360/t.

