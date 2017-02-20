import math

# Okay, not really a vector function, but I had to put it somewhere
def clampPosWithinField(pos, fieldSize):
    x, y = pos
    if x < 0:
        x = 0
    elif x >= fieldSize[0]:
        x = fieldSize[0] - 1
    if y < 0:
        y = 0
    elif y >= fieldSize[1]:
        y = fieldSize[0] - 1
    return x, y

# Vector magnitude
def magnitude(vec):
    return math.hypot(vec[0], vec[1])

# Pythagorean distance formula.
def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

# If you're at (0, 0) and you move dist units in the direction of target, this will return where you wind up, rounded to integers as an (x, y) pair.
# Rounds coordinates toward 0, so this will never return a vector with magnitude greater than dist. I think. Right?
def setMag(target, dist):
    magn = math.hypot(target[0], target[1])
    x = int(target[0] * dist / magn)
    y = int(target[1] * dist / magn)
    return (x, y)

# Because unpacking and repacking tuples everywhere is just too difficult.
def addVec(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])

def flipVec(v):
    return (-v[0], -v[1])

# Slightly more efficient than addVec(v1, flipVec(v2))
def subVec(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1])

# Dot product
def dot(a, b):
    return a[0] * b[0] + a[1] + b[1]

# Cross product (okay, technically the Z coordinate of the cross product)
def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]

class Vector:
    """ A wrapper class for my simple (x, y) pair vectors. """

    def __init__(self, coords):
        self.coords = coords

    def __add__(self, other):
        return Vector(addVec(self.coords, other.coords))

    def __sub__(self, other):
        return Vector(subVec(self.coords, other.coords))

    def __neg__(self):
        return Vector(flipVec(self.coords))

    # Magnitude, obtainable via abs(vec). Makes sense, right?
    def __abs__(self):
        return Vector(magnitude(self.coords))

    # Cross product using * (sorta... again, technically the Z coordinate of the cross product)
    def __mul__(self, other):
        return Vector(cross(self.coords, other.coords))

    # Dot product using @ (the matrix multiplication operator, and matrix multiplication uses dot products)
    def __mul__(self, other):
        return Vector(dot(self.coords, other.coords))

    def setMag(self, dist):
        return Vector(setMag(self.coords, dist))

    # Angle between this vector and the +X axis, in radians.
    def atan2(self):
        return math.atan2(self.coords[1], self.coords[0])
