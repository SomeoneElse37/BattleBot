from calc.vector import *

# Parse a string formatted like '4E', returning an (x, 0) or (0, y) pair, or raises a ValueError is the format is incorrect
def parseCoord(strn):
    char = strn[-1].lower()
    num = int(strn[:-1]) if len(strn) > 1 else 1
    if char == 'n':
        return (0, num)
    elif char == 's':
        return (0, -num)
    elif char == 'w':
        return (-num, 0)
    elif char == 'e':
        return (num, 0)
    else:
        raise ValueError('Improper coordinate format: ' + strn)

# Takes in a list of strings, and greedily parses the first one or two, returning ((x, y), rest_of_codex) or (None, codex)
def parseDirection(codex):
    try:
        coord1 = parseCoord(codex[0])
    except (ValueError, IndexError):
        return None, codex
    try:
        coord2 = parseCoord(codex[1])
    except (ValueError, IndexError):
        return coord1, codex[1:]
    if (coord1[0] == 0 and coord2[1] == 0) or (coord1[1] == 0 and coord2[0] == 0):
        return addVec(coord1, coord2), codex[2:]
    return coord1, codex[1:]

