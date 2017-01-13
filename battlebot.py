# discord.py
# Base code by Eruantien
# ANWA-apecific code by Someone Else 37

#import asyncio
import discord
import logging
import time
import math
import traceback
import pickle

from sys import argv
from random import randint, gauss

from statistics import *
from datetime import *

def d10(times, sides):
    dice_list = []
    for foo in range(0, times):
        bar = randint(1, sides)
        dice_list += [bar]
    return(dice_list)

def formatRoll(rolls):
    return(str(sum(rolls)) + ' = ' + str(rolls))

def roll(codex):
    codex = codex[0].split('d')
    return(formatRoll(d10(int(codex[0]), int(codex[1]))))

# Emulates rolling n d10s and adding the results by way of the Gaussian function above, and returns the simulated sum.
# Th weird constants and stuff come from the Central Limit Theorem. Go look it up, if you're so inclined.
def statisticD10Sum(n):
    return max(0, round(gauss(5.5, math.sqrt(8.25) / math.sqrt(n)) * n))

# Rolls N d10s and returns the result. If N <= 300, will call d10() and formatRoll(), literally rolling a bunch of virtual d10s.
# If N > 300, will instead use statistical methods to simulate rolling the dice, to save on CPU time and message length.
# if given secret=True as a parameter, will not report the number of dice rolled.
# In any case, returns a pair, (log, sum) of the sum of the dice rolled and a human-readable log of the rolls themselves
def prettyRoll(n, secret=False):
    if not secret:
        if n <= 300:
            rolls = d10(n, 10)
            return formatRoll(rolls), sum(rolls)
        else:
            roll = statisticD10Sum(n)
            return '{:d} = [... x{:d} ...]'.format(roll, n), roll
    else:
        roll = 0                    # The Central Limit Theorem really kicks in with a sample size >= 30,
        if n <= 30:                 # if the underlying distribution is not heavily skewed.
            roll = sum(d10(n, 10))  # Hence why I use 30 here.
        else:
            roll = statisticD10Sum(n)
        return '{:d} = [...]'.format(roll), roll

accCheckFlavors = [
        'The attack missed by a mile.',
        'Failure. The attack missed.',
        'Success! The attack connects.',
        'Critical hit? Maybe?'
        ]

aglCheckFlavors = [
        'No. Not even close.',
        "Couldn't quite escape melee range.",
        'Just made it out of melee range.',
        'Easily escaped melee range.'
        ]

def checkString(r1, r2, flavors=accCheckFlavors):
    diff = r1 - r2
    if diff < -20:
        return flavors[0]
    elif diff <= 0:
        return flavors[1]
    elif diff <= 20:
        return flavors[2]
    else:
        return flavors[3]

def formatCheck(atk, dfn):
    r1 = sum(atk)
    r2 = sum(dfn)
    diff = r1 - r2
    out = formatRoll(atk) + '\n' + formatRoll(dfn) + '\n'
    return out + checkString(r1, r2)

def check(codex):
    return formatCheck(d10(int(codex[0]), 10), d10(int(codex[1]), 10))

# Rolls an accuracy check, using modern dice-rolling and secret-handling technology. Optional keyword argument called secrets
# takes a pair of booleans, defaulting to (False, False). If secrets[0] is True, the number of Accuracy dice rolled will not be reported;
# if secrets[1] is true, the number of Evasion dice will not be reported.
def prettyCheck(acc, eva, secrets=(False, False), flavors=accCheckFlavors):
    s1, r1 = prettyRoll(acc, secrets[0])
    s2, r2 = prettyRoll(eva, secrets[1])
    return s1 + '\n' + s2 + '\n' + checkString(r1, r2, flavors=flavors), r1 > r2

# Used in the command that rolls damage a bunch of times. Yes, I'm duplicating code, sue me.
def calcDamage(atk, dfn):   # Takes the attack and defense STATS as parameters (not rolls)
    r1 = sum(d10(atk, 10))
    r2 = sum(d10(dfn, 10))
    ratio = r1 / r2
    return math.ceil(ratio - 1)

def damageString(r1, r2):
    ratio = r1 / r2
    dmg = math.ceil(ratio - 1)
    out = "{:d}%: ".format(int(ratio * 100))
    if dmg == 0:
        return out + "The attack was blocked.", 0
    else:
        return out + "The attacker dealt " + str(dmg) + " damage.", dmg

def formatDamage(atk, dfn):
    r1 = sum(atk)
    r2 = sum(dfn)
    out = formatRoll(atk) + '\n' + formatRoll(dfn) + '\n'
    dmgstr, dmg = damageString(r1, r2)
    return out + dmgstr, dmg

def damage(codex):
    return(formatDamage(d10(int(codex[0]), 10), d10(int(codex[1]), 10))[0])

def prettyDamage(atk, dfn, secrets=(False, False)):
    s1, r1 = prettyRoll(atk, secrets[0])
    s2, r2 = prettyRoll(dfn, secrets[1])
    dmgstr, dmg = damageString(r1, r2)
    return s1 + '\n' + s2 + '\n' + dmgstr, dmg

partialchars = {
        1: '.',
        2: ':',
        3: ':.',
        4: '::',
        5: '|',
        6: '|.',
        7: '|:',
        8: '|:.',
        9: '|::'
        }

def histogram(rolls):
    hist = [0]*(max(rolls) + 1)
    for r in rolls:
        hist[r] += 1
    out = ""
    for i in range(0, len(hist)):
        out += "`{:<2d}: ".format(i) + ("#" * (hist[i] // 10)) + partialchars.get(hist[i] % 10, '') + "`\n"
    return out

def summary(rolls):
    maximum = max(rolls)
    minimum = min(rolls)
    theMode = 0
    try:
        theMode = mode(rolls)
    except StatisticsError:
        theMode = "N/A"
    out = "Mean: {:.3f}, Median: {}, Mode: {}, Range: {}\n".format(mean(rolls), median(rolls), theMode, maximum - minimum)
    return out + "Minimum: {}, Maximum: {}, Standard Deviation: {:.3f}".format(minimum, maximum, pstdev(rolls))

def testStatisticRolls(codex):
    n = int(codex[0])
    bucketSize = int(codex[1])
    diceRolls = []
    statRolls = []
    for i in range(500):
        diceRolls += [sum(d10(n, 10))]
        statRolls += [statisticD10Sum(n)]
    out = 'For the count-and-add computation:\n' + summary(diceRolls)
    out += '\n\nFor the fancy statistical computation:\n' + summary(statRolls)
    diceRolls = [(x // bucketSize) * 2 for x in diceRolls]
    statRolls = [(x // bucketSize) * 2 + 1 for x in statRolls]
    theHist = histogram(diceRolls + statRolls)
    return out + '\n\nEven rows are from rolling dice conventionally; odd rows from my new statistical technique\n' + theHist

def averagedamage(codex):
    atk = int(codex[0])
    dfn = int(codex[1])
    rolls = []
    for i in range(1000):
        rolls += [calcDamage(atk, dfn)]
    out = summary(rolls) + "\n"
    out += histogram(rolls)
    rolls = [x for x in rolls if x > 0]
    if len(rolls) > 0:
        out += "\nWhen ignoring zero-damage rolls:\n"
        out += summary(rolls)
    return out

def runAttack(acc, atk, eva, dfn, hp): #Yes, WET code again. This would be easier to make DRY in a lazy language...
    turns = 0
    while hp > 0:
        turns += 1
        if turns > 30:
            return 0
        if sum(d10(acc, 10)) > sum(d10(eva, 10)):
            hp -= calcDamage(atk, dfn)
    return turns

def runAttackWithLog(acc, atk, eva, dfn, hp):
    turns = 0
    log = "{:d} HP\n".format(hp)
    while hp > 0:
        turns += 1
        if turns > 30:
            return "Battle took too long. Defender reduced to {} HP after 30 turns.".format(hp)
        log += "---Turn {:d}---\n".format(turns)
        accRoll = d10(acc, 10)
        evaRoll = d10(eva, 10)
        log += formatCheck(accRoll, evaRoll).replace("\n", "   ") + "\n"
        if sum(accRoll) > sum(evaRoll):
            atkRoll = d10(atk, 10)
            dfnRoll = d10(dfn, 10)
            report, damage = formatDamage(atkRoll, dfnRoll)
            hp -= damage
            log += report.replace("\n", "   ") + "\n"
            if damage > 0:
                log += "{:d} HP\n".format(hp)
    log += "{:d} turns taken to KO.".format(turns)
    if len(log) > 2000:
        return "Combat log too long. Defender reduced to {} HP after {} turns.".format(hp, turns)
    return log

def attack(codex):
    return runAttackWithLog(int(codex[0]), int(codex[1]), int(codex[2]), int(codex[3]), int(codex[4]))

def repattack(codex):
    acc, atk, eva, dfn, hp = int(codex[0]), int(codex[1]), int(codex[2]), int(codex[3]), int(codex[4])
    rolls = []
    for i in range(1000):
        rolls += [runAttack(acc, atk, eva, dfn, hp)]
    totalBattles = len(rolls)
    rolls = [x for x in rolls if x > 0]
    shortBattles = len(rolls)
    if len(rolls) > 0:
        out = summary(rolls) + "\n" + histogram(rolls)
        if totalBattles != shortBattles:
            out += "\n{} battles of {} not shown.".format(totalBattles - shortBattles, totalBattles)
        return out
    else:
        return "All {} battles took more than 30 turns.".format(totalBattles)

rangeNames = {
        0: 'Boxing Range',  # 0-15
        1: 'Sword Range',   # 16-31
        2: 'Pike Range',    # 32-64
        3: 'Javelin Range', # etc.
        4: 'Shortbow Range',
        5: 'Longbow Range',
        6: 'Unaided Eyesight',
        7: 'Telescope Range',
        8: 'Intercontinental Range'
        }

BASE_RANGE = 2      # The miminum distance, in range units, considered to be in Sword Range
HIGHEST_RANGE_KEY = len(rangeNames) - 1
BOXING_MAX = BASE_RANGE - 1     # Deprecated. Used when checking that basic physical attacks can actually be done

def rangestring(rangeInt):
    n = min((rangeInt // BASE_RANGE).bit_length(), HIGHEST_RANGE_KEY)
    return rangeNames[n]

def rangedump():
    out = '0-{:d}: {:s}\n'.format(BASE_RANGE - 1, rangeNames[0])
    n = BASE_RANGE
    for i in range(1, HIGHEST_RANGE_KEY):
        out += '{:d}-{:d}: {:s}\n'.format(n, n*2 - 1, rangeNames[i])
        n *= 2
    out += '{:d}+: {:s}'.format(n, rangeNames[HIGHEST_RANGE_KEY])
    return out

def rangeReverseLookup(strn):
    for i in range(0, 9):
        if strn.lower() in rangeNames[i].lower():
            if i == 0:
                return 0
            else:
                return 2**(i-1) * BASE_RANGE
    raise ValueError('There is no such range as ' + strn + '!')

def stringsToRange(minimum, maximum):
    a = rangeReverseLookup(minimum)
    b = rangeReverseLookup(maximum)
    if b == 0:
        b = BASE_RANGE - 1
    elif b == 2 ** (HIGHEST_RANGE_KEY - 1) * BASE_RANGE:
        b = -1
    else:
        b = b * 2 - 1
    return a, b

def checkrange(codex):
    return(rangestring(int(codex[0])))

def checkRangeReverse(codex):
    a, b = stringsToRange(codex[0], codex[0])
    if b == -1:
        return '{:s}: {:d}+'.format(rangestring(a), a)
    else:
        return '{:s}: {:d}-{:d}'.format(rangestring(a), a, b)

def formatRetreat(r, spd):
    dx = sum(spd)
    return formatRoll(spd) + '\n' + str(dx) + ': Moved from ' + str(r) + ' (' + rangestring(r) + ') to ' + str(r + dx) + ' (' + rangestring(r + dx) + ').'

def prettyRetreat(r, spd, limit=-1, secret=False):
    s1, r1 = prettyRoll(spd, secret=secret)
    newR = r + r1
    if limit > 0 and newR > limit:
        newR = limit
    return "{:s}\n{:d}: Moved from {:d} ({:s}) to {:d} ({:s}).".format(s1, r1, r, rangestring(r), newR, rangestring(newR)), newR

def calcRetreat(codex):
    return(formatRetreat(int(codex[0]), d10(int(codex[1]), 10)))

def approachCenter(r, spd):
    dx = sum(spd)
    return formatRoll(spd) + '\n' + str(dx) + ': Moved from ' + str(r) + ' (' + rangestring(r) + ') to ' + str(max(0, r - dx)) + ' (' + rangestring(r - dx) + ').'

def prettyApproachCenter(r, spd, limit=-1, secret=False):
    s1, r1 = prettyRoll(spd, secret=secret)
    newR = max(0, limit, r - r1)
    return "{:s}\n{:d}: Moved from {:d} ({:s}) to {:d} ({:s}).".format(s1, r1, r, rangestring(r), newR, rangestring(newR)), newR

def prettyApproachChar(r1, spd, r2, limit=-1, secret=False):
    out, dx = prettyRoll(spd, secret=secret)
    # dx = sum(spd)
    rangediff = abs(r1 - r2)
            # For 1..dx, subtract 1 from r1 or r2, whichever is bigger.
            #
            # If dx > rangediff:
            #   Set the bigger range equal to the smaller one
            #   then subtract (dx - rangediff)/2 from both
            #   then subtract 1 from r1, if (dx-rangediff) was odd.
            # If dx <= rangediff:
            #   Subtract dx from the bigger range.
    r1final = r1
    r2final = r2
    if dx > rangediff:
        if r1 > r2:
            r1final = r2
        else:
            r2final = r1
        r1final -= int((dx - rangediff) / 2) - (dx - rangediff) % 2
        r2final -= int((dx - rangediff) / 2)
    else:
        if r1 > r2:
            r1final = r1 - dx
        else:
            r2final = r2 - dx
    r1final = max(0, limit, r1final)
    r2final = max(0, limit, r2final)
    out += '\n{:d}: Pursuer moved from {:d} ({:s}) to {:d} ({:s}).'.format(dx, r1, rangestring(r1), r1final, rangestring(r1final))
    out += '\n Target moved from {:d} ({:s}) to {:d} ({:s}).'.format(r2, rangestring(r2), r2final, rangestring(r2final))
    return out, r1final, r2final

def calcApproach(codex):
    if len(codex) <= 2:
        return approachCenter(int(codex[0]), d10(int(codex[1]), 10))
    else:
        return prettyApproachChar(int(codex[0]), int(codex[1]), int(codex[2]))

def magnitude(vec):
    return math.hypot(vec[0], vec[1])

# Pythagorean distance formula.
def distance(pos1, pos2):
    return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

# If you're at (0, 0) and you move dist units in the direction of target, this will return where you wind up, rounded to integers as an (x, y) pair.
# Rounds coordinates toward 0, so this will never return a vector with magnitude greater than magn. I think. Right?
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

# Used to move a point into the battlefield, if it is not already
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


##################################################
##### Code for moderated battles begins here #####
##################################################

sizeTiers = {
        'faerie': 1,
        'elf': 2,
        'werecat': 2,
        'elfcat': 2,
        'cyborg': 2,
        'robot': 2,
        'kraken': 3,
        'elfship': 3,
        'steamship': 3
        }


def makeStatDict(hp, acc, eva, atk, dfn, spd):
    return dict(HP=hp, ACC=acc, EVA=eva, ATK=atk, DEF=dfn, SPD=spd)

def makeStatsFromCodex(codex):
    if len(codex) >= 6:
        return makeStatDict(int(codex[0]), int(codex[1]), int(codex[2]), int(codex[3]), int(codex[4]), int(codex[5]))
    else:
        return makeStatDict(0, 0, 0, 0, 0, 0)

def defaultStats(size):
    return makeStatDict(2**(size * 2), 2**(-size + 5), 2**(-size + 5), 2**(size * 4 - 2), 2**(size * 2), 2**(size))

baseStats = {
        'faerie': defaultStats(sizeTiers['faerie']),    # This sets the base stats for each species to the default, computed from their size.
        'elf': defaultStats(sizeTiers['elf']),          # If Lens wants different base stats for any/all races, I can hardcode that easily.
        'human': defaultStats(sizeTiers['elf']),        # Allowing GMs to set that up per-server is doable, but would take a bit more work.
        'werecat': defaultStats(sizeTiers['werecat']),
        'elfcat': defaultStats(sizeTiers['elfcat']),
        'cyborg': defaultStats(sizeTiers['cyborg']),
        'robot': defaultStats(sizeTiers['robot']),
        'kraken': defaultStats(sizeTiers['kraken']),
        'elfship': defaultStats(sizeTiers['elfship']),
        'steamship': defaultStats(sizeTiers['steamship']),
        }

def statstring(stats):
    return "HP: {:d}  Accuracy: {:d}  Evasion: {:d}  Attack: {:d}  Defense: {:d}  Speed: {:d}".format(stats['HP'], stats['ACC'], stats['EVA'], stats['ATK'], stats['DEF'], stats['SPD'])

# I can use objects instantiated from a class that hasn't been defined yet, as long as I don't explicitly refer to that class, right?
class Modifier:
    """Represents a modifier, and stores all the data needed for one."""

    def getHolderMods(self):
        pair = self.holder.modifiers[self.stat]
        return pair[0 if self.isMult else 1]

    def regWithHolder(self, holder=None):
        if self.holder is None:
            self.holder = holder
        if self.holder is not None:
            self.getHolderMods().append(self)

    def regWithOwner(self, owner=None):
        if self.owner is None:
            self.owner = owner
        if self.owner is not None:
            self.owner.ownedModifiers.append(self)

    def __init__(self, stat, factor=None, duration=None, isMult=None, holder=None, owner=None):
        if factor is None and duration is None and isMult is None:
            stat, factor, duration, isMult = stat   # Permit the first argument to be a tuple containing (stat, factor, duration, isMult), and ignoring the rest
        self.stat = stat.upper()
        self.factor = factor
        self.duration = duration
        self.isMult = isMult
        self.holder = holder
        self.owner = owner
        self.regWithHolder()    # No-op if holder is None
        self.regWithOwner()     # Ditto for owner

    def revoke(self):
        try:
            if self.holder is not None:
                self.getHolderMods().remove(self)
            if self.owner is not None:
                self.owner.ownedModifiers.remove(self)
        except (AttributeError, ValueError) as e:       # Shouldn't be needed in the future, but the database got borked in testing
            print('Something weird happened while trying to revoke a modifier:\n' + str(e))

    def tick(self):
        if self.duration == 0:
            self.revoke()
        elif self.duration > 0:
            self.duration -= 1

    def __eq__(self, other):
        return self is other

    def __str__(self):
        if self.isMult:
            return '{:d}% ({:d})'.format(int(self.factor * 100), self.duration)
        else:
            return '{:+d} ({:d})'.format(self.factor, self.duration)

    __repr__ = __str__

def sumThings(xs, data):
    total = sum(xs)
    return total, '{:d} = {!s}'.format(total, xs)

def rollAccCheckForRPN(xs, data):
    log, hit = prettyCheck(xs[0], xs[1], data['secrets'])
    return (1 if hit else 0), log

# Any data that parseRPN() could be expected to be able to look up from the beginning
# By default, considers both "characters'" stats to be visible (because they don't really have stats to hide)
baseData = {'secrets': (False, False)}

# Operators and functions that parseRPN should have access to, even without any character context
baseFunctions = {'+': (2, lambda xs, data: (xs[0] + xs[1], '')),
        '-': (2, lambda xs, data: (xs[0] - xs[1], '')),
        '*': (2, lambda xs, data: (xs[0] * xs[1], '')),
        '/': (2, lambda xs, data: (xs[0] // xs[1], '')),
        'sum': (-1, sumThings),
        'roll': (1, lambda xs, data: prettyRoll(xs[0])[::-1]),                          # Rolls some d10s. Simple enough.
        'rollh': (1, lambda xs, data: prettyRoll(xs[0], True)[::-1]),                   # Rolls some d10s, but hides the actual rolls.
        'rollu': (1, lambda xs, data: prettyRoll(xs[0], data['secrets'][0])[::-1]),     # Hides the actual rolls if and only if the user's stats are hidden.
        'rollt': (1, lambda xs, data: prettyRoll(xs[0], data['secrets'][1])[::-1]),     # Hides the actual rolls if and only if the target's stats are hidden.
        'rollacc': (2, rollAccCheckForRPN),
        'calcdmg': (2, lambda xs, data: damageString(xs[0], xs[1])[::-1]),
        'rolldmg': (2, lambda xs, data: prettyDamage(xs[0], xs[1], data['secrets'])[::-1])}

# Parses an RPN codex, with the specified context. data and functions will be merged with baseData and baseFunctions,
# with the data and functions having precedence if any of the keys conflict.
def parseRPN(codex, data = {}, functions = {}):
    codex = [s.lower() for s in codex]
    data = {**baseData, **data}
    functions = {**baseFunctions, **functions}
    stack = []
    log = ''
    for op in codex:
        try:
            stack.append(int(op))
        except ValueError:
            if op in data:
                stack.append(data[op])
            elif op in functions:
                args, fn = functions[op]
                par = []
                if args >= 0:
                    for i in range(args):
                        par.append(stack.pop())
                        par = par[::-1]
                else:
                    par = stack
                    stack = []
                retval, note = fn(par, data)
                stack.append(retval)
                if len(note) > 0:
                    log += '\n' + note
            else:
                stack.append(op)
    if len(stack) == 1:
        return stack[0], log
    else:
        raise ValueError('Expected stack to contain exactly one item after execution; got ' + str(stack))

def testRPN(codex):
    retval, log = parseRPN(codex)
    return log + '\n\n' + str(retval)

# These functions are formatted the same way as baseFunctions, but are aimed for use in abilities.
auxFunctions = {
        'hp':  (1, lambda xs, data: (xs[0].hp(), '')),
        'acc': (1, lambda xs, data: (xs[0].acc(), '')),
        'eva': (1, lambda xs, data: (xs[0].eva(), '')),
        'atk': (1, lambda xs, data: (xs[0].atk(), '')),
        'def': (1, lambda xs, data: (xs[0].dfn(), '')),
        'spd': (1, lambda xs, data: (xs[0].spd(), '')),
        'health': (1, lambda xs, data: (xs[0].health, '')),
        'pos': (1, lambda xs, data: (xs[0].pos, '')),
        'dist': (2, lambda xs, data: (distance(xs[0], xs[1]), '')),
        '+mod': (3, lambda xs, data: ((xs[1], xs[0], xs[2], False), '')),
        '-mod': (3, lambda xs, data: ((xs[1], -xs[0], xs[2], False), '')),
        'mod%': (3, lambda xs, data: ((xs[1], xs[0] / 100, xs[2], True), '')),
        '+mod%': (3, lambda xs, data: ((xs[1], 1 + xs[0] / 100, xs[2], True), '')),
        '-mod%': (3, lambda xs, data: ((xs[1], 1 - xs[0] / 100, xs[2], True), '')),
        }

class Ability:
    """Represents an Ability that a character may call upon at any time. On their turn, at least."""

    # Codex format: abilityName range cooldown ((self | ally | enemy)+ | location) [limit]
    def setFields(self, codex):
        codex = [s.lower() for s in codex]
        self.name = codex[0]
        self.range = int(codex[1])
        self.cooldown = int(codex[2])
        if codex[3] == 'location':
            self.targets = {'location'}
            self.limit = int(codex[4])
        else:
            self.targets = set()
            i = 3
            try:
                while codex[i] in {'self', 'ally', 'enemy'}:
                    self.targets.add(codex[i])
                    i += 1
                self.limit = int(codex[-1])
            except IndexError:  # No limit was given
                self.limit = 1  # so, by default, will only permit one target


    def __init__(self, codex):
        self.setFields(codex)
        self.steps = []

    # Each element in steps is a list of strings. The first is always 'calc', 'condition', or 'effect'.
    # The second varies.
    #   For calc, it's the name of the variable to be calculated and assigned.
    #   For effect, it's what the effect is and who to apply it to (defaulting to 'target').
    #   For condition, it's what to compare to (defaulting to '>0'), because
    # In all cases, the above is followed by an RPN string wrapped up in a single list, describing what to calculate.
    # This method takes a codex, in slightly-more-flexible user-friendly syntax, formats it as above, and returns it.
    def parseStep(self, codex):
        out = []
        codex = [s.lower() for s in codex]
        if codex[0] == 'calc':
            out = codex[:2]
            codex = codex[2:]
        elif codex[1] == '=':
            out = ['calc', codex[0]]
            codex = codex[2:]
        elif codex[0] == 'condition':
            out = codex[0]
            if codex[1] in {'>0', '=0', '<0', '~0', '>=0', '<=0'}:
                out.append(codex[1])
                codex = codex[2:]
            elif codex[1] == '==0':
                out.append('=0')
                codex = codex[2:]
            elif codex[1] in {'!0', '!=0', '~=0'}:
                out.append('~0')
                codex = codex[2:]
            else:
                out.append('>0')
                codex = codex[1:]
        elif codex[0] == 'effect':
            out = codex[0]
            codex = codex[1:]
            if codex[0] in {'damage', 'apply'}:
                out.append(codex[0])
                codex = codex[1:]
            else:
                codex.append('apply')
            if codex[0] in {'self', 'target'}:
                out.append(codex[0])
                codex = codex[1:]
            else:
                out.append('target')
        out.append(codex)
        return out


    # Parameter to this method is the codex, straight from user input, with the keywords leading to this ability stripped off the front.
    def setStep(self, codex):
        try:
            i = int(codex[0])
            self.steps[i] = self.parseStep(codex[1:])
        except ValueError:
            name = ''
            if codex[0] == 'calc':
                name = codex[1]
            elif codex[1] == '=':
                name = codex[0]
            if name != '':
                for i, step in enumerate(self.steps):
                    if step[0] == 'calc' and step[1] == name:
                        self.steps[i] = self.parseStep(step)
                        return
            self.steps.append(self.parseStep(codex))

class Character:
    """Represents a character known to BattleBot."""

    def clearModifiers(self):
        if hasattr(self, 'modifiers'):
            for pair in self.modifiers.values():
                for mods in pair:
                    for m in mods:
                        m.holder = None
                        m.revoke()
        self.modifiers = dict(HP=([], []), ACC=([], []), EVA=([], []), ATK=([], []), DEF=([], []), SPD=([], []))

    # Attributes: username, userid, name, race, size, statPoints, baseStats, abilities, modifiers, health, location, secret
    def __init__(self, owner, name, race, statpoints, secret=False):
        if not race in sizeTiers:
            raise ValueError("Invalid race.")
        self.username = owner.mention
        self.userid = owner.id
        self.name = name
        self.race = race.lower()
        self.size = sizeTiers[self.race]
        self.statPoints = statpoints
        self.baseStats = baseStats[self.race]
        # Modifiers are stored in this dictionary.
        # The keys are the same as in all the various stat dictionaries. HP, ACC, EVA, etc.
        # Each value is a pair of lists. The first element in each pair is a list of multiplicative modifiers (e.g. 120% STR for 2 turns);
        # and the second element is a list of additive modifiers (e.g. +20 ACC until end of battle).
        # Each entry in these lists is itself a pair. The first element of this pair is the amount that the modifier changes the stat.
        # The second element is the duration of the modifier. This will be decremented at the end of each turn, and when it drops below zero, the modifier is removed.
        # Negative durations last forever.
        self.clearModifiers()
        self.ownedModifiers = []
        #self.abilities = []     # Ability system is planned, but NYI
        self.health = self.hp()
        self.pos = (0, 0)       # X and Y coordinates
        self.secret = secret    # If true, this character's stats will not be reported to players (used for some NPCs)

    # # (stat, factor, duration, isMult)
    # def createModifier(self, theTuple):
    #     stat, factor, duration, isMult = theTuple
    #     pair = self.modifiers[stat]
    #     mods = pair[0 if isMult else 1]
    #     mods.append((factor, duration))

    def listModifiers(self):
        out = ''
        for stat in ['HP', 'ACC', 'EVA', 'ATK', 'DEF', 'SPD']:
            mults, adds = self.modifiers[stat]
            if len(mults) > 0 or len(adds) > 0:
                out += '{}: {!s}\n'.format(stat, mults + adds)
            # if len(mults) > 0:
            #     for f, d in mults:
            #         out += '{:d}% {:s} ({:d})   '.format(int(f * 100), stat, d)
            #     out += '\n'
            # if len(adds) > 0:
            #     for f, d in adds:
            #         out += '{:+d} {:s} ({:d})   '.format(f, stat, d)
            #     out += '\n'
        return out

    def multModifiers(self, stat):
        mods = self.modifiers[stat][0]
        product = 1
        for m in mods:
            product *= m.factor
        return product

    def addModifiers(self, stat):
        mods = self.modifiers[stat][1]
        total = 0
        for m in mods:
            total += m.factor
        return total

    def calcStat(self, stat):
        return int(self.baseStats[stat] * (1 + self.statPoints[stat] / 8) * self.multModifiers(stat) + self.addModifiers(stat))

    # Returns the characters hp STAT, i.e. their MAXIMUM health, NOT their current health. Use the self.health attribute for that.
    def hp(self):
        return self.calcStat('HP')

    # Return the character's current Accuracy, accounting for all modifiers
    def acc(self):
        return self.calcStat('ACC')

    def eva(self):
        return self.calcStat('EVA')

    def atk(self):
        return self.calcStat('ATK')

    def dfn(self):
        return self.calcStat('DEF')

    def spd(self):
        return self.calcStat('SPD')

    def currentStats(self):
        return makeStatDict(self.hp(), self.acc(), self.eva(), self.atk(), self.dfn(), self.spd())

    def tickModifiers(self):
        for m in self.ownedModifiers:
            m.tick()

    def __str__(self):
        s1 = '...'
        s2 = '...'
        if not self.secret:
            s1 = statstring(self.statPoints)
            s2 = statstring(self.currentStats())
        return """Owner's username: {:s}
Owner's UUID: {:s}
Name: {:s}
Race: {:s}
Size Tier: {:d}
Stat Points: [{:s}]
Current Stats: [{:s}]
Location: ({:d}, {:d})
Health: {:d}""".format(self.username, self.userid, self.name, self.race, self.size, s1, s2, self.pos[0], self.pos[1], self.health)

    # Reset health to the maximum, and clear all modifiers.
    def respawn(self):
        self.health = self.hp()
        self.clearModifiers()

    # Rolls an accuracy check against this character. Used in some of the methods below, and I plan to make this available to GMs
    # directly for special attacks.
    def rollAccuracy(self, acc, secret=False):
        # accRolls = d10(acc, 10)
        # evaRolls = d10(self.eva(), 10)
        # return formatCheck(accRolls, evaRolls), sum(accRolls) > sum(evaRolls)
        return prettyCheck(acc, self.eva(), secrets=(secret, self.secret))

    # Rolls an attack with the given Attack stat against this character. Used by the bot's GMing code, and I plan
    # to add a command to allow GMs to use this directly for special attacks.
    def rollDamage(self, atk, secret=False):
        # atkRolls = d10(atk, 10)
        # defRolls = d10(self.dfn(), 10)
        # out, damage = formatDamage(atkRolls, defRolls)
        out, damage = prettyDamage(atk, self.dfn(), secrets=(secret, self.secret))
        self.health -= damage
        if self.health <= 0:
            out += '\n\n' + self.name + ' has been struck down.'
            # Caller can look at self.health to see if they need to be respawned and removed from the battle.
        else:
            out += '\n\n' + self.name + ' has ' + str(self.health) + ' HP remaining.'
        return out, damage

    # Rolls an accuracy check against this character, then, if that passes, rolls for damage. Basically just combines the
    # above two methods.
    def rollFullAttack(self, acc, atk, secret=False):
        accStr, success = self.rollAccuracy(acc, secret=secret)
        if success:
            dmgStr, damage = self.rollDamage(atk, secret=secret)
            return accStr + '\n\n' + dmgStr, damage
        else:
            return accStr, 0

    # Movement ability. Roll speed, then move the Character's coordinates along the specified [(dx, dy), ...] path, up to the maximum distance.
    # If maxDist is positive, the Character will try to move exactly that distance, continuing beyond the end of the path if necessary and ignoring the stop parameter.
    # If stop == False, when the Character reaches the end of the path, they will continue moving in that direction as far as the speed roll and maxDist permit.
    # size is the size of the battlefield
    def testMove(self, path, maxDist, stop, size):
        out, dist = prettyRoll(self.spd(), secret=self.secret)
        pos = self.pos
        if maxDist >= 0:        # Set the distance to travel to either the roll or the maxDist parameter, if given, whichever is less.
            dist = min(dist, maxDist)
            stop = False
        elif stop:    # If the character is intended to stop at the end of the path, ensure that the last waypoint is "go nowhere"
            path.append((0, 0))
        for i in range(len(path) - 1):  # Last coordinate in the path is treated differently, so don't iterate through it here
            mag = magnitude(path[i])
            if mag >= dist:
                pos = addVec(pos, setMag(path[i], dist))
                dist = 0
                break
            else:
                pos = addVec(pos, path[i])
                dist -= mag
        if dist > 0 and magnitude(path[-1]) > 0:        # If character can travel any farther and the last waypoint isn't "go nowhere",
            pos = addVec(pos, setMag(path[-1], dist))   # move character in the direction of the last waypoint as far as possible
        pos = clampPosWithinField(pos, size)
        return out + '\nMoved from {!s} to {!s}'.format(self.pos, pos), pos

    # Will be fancier once abilities are in
    def canMelee(self, pos):
        return distance(pos, self.pos) < BASE_RANGE

    def inBox(self, minX, maxX, minY, maxY):
        return minX <= self.pos[0] <= maxX and minY <= self.pos[1] <= maxY

    # # Retreat ability. Roll speed, and add the result to this chracter's location. Return (logstring, newLocation)
    # def retreat(self, limit=-1):
    #     out, self.location = prettyRetreat(self.location, self.spd(), limit=limit, secret=self.secret)
    #     return out, self.location

    # # Target-free approach ability. Roll speed, and subtract the result from this chracter's location. Return (logstring, newLocation)
    # def approachCenter(self, limit=-1):
    #     out, self.location = prettyApproachCenter(self.location, self.spd(), limit=limit, secret=self.secret)
    #     return out, self.location

    # # Targeted approach ability. Roll speed, and move the user and the target toward the center. This character is the PURSUER, NOT the target.
    # # Return (logString, newUserLocation, newTargetLocation)
    # def approachChar(self, target, limit=-1):
    #     out, self.location, target.location = prettyApproachChar(self.location, self.spd(), target.location, limit=limit, secret=self.secret)
    #     return out, self.location, target.location

    def __eq__(self, other):
        return self.userid == other.userid and self.name == other.name

class Battle:
    """Corresponds to a Guild, and stores a list of characters within that Guild as well as who's participating in the battle, turn order, etc."""

    # Attributes: characters, participants, turn, id, name, radius
    def __init__(self, guild):
        self.characters = {}    # Dictionary of Characters on the server, keyed by character's lowercased name
        self.participants = []  # List of Characters participating in current battle, ordered by initiative
        self.turn = -1          # participants[turn] = the Character whose turn it is
        self.id = guild.id      # Guild ID
        self.name = guild.name  # Guild Name
        self.size = (2048, 2048)
        self.moved = false      # True if the current character has /moved during their turn
        self.attacked = false   # True if the current character has /attacked or used an /ability during their turn
        self.orphanModifiers = []

    def addCharacter(self, char):
        if char.name.lower() not in self.characters:
            self.characters[char.name.lower()] = char
        else:
            raise ValueError("There is already a character named " + char.name + "!")

    def clear(self):
        for k, v in self.characters.items():
            v.respawn()
        self.participants = []
        self.turn = -1
        for m in self.orphanModifiers:
            m.revoke()
        self.orphanModifiers = []

    # Warning: May give undefined behavior if char is not already in the characters dictionary
    def addParticipantByChar(self, char):
        if char in self.participants:
            raise ValueError(char.name + " is already participating!")
        else:
            firstEq = -1
            firstLess = -1
            for i in range(len(self.participants)):
                if self.participants[i].spd() < char.spd():
                    firstLess = i
                    break
                elif self.participants[i].spd() == char.spd() and firstEq == 0:
                    firstEq = i
            if firstEq == -1 and firstLess == -1: # All other participants are faster than char
                self.participants.append(char)
            elif firstEq == -1: # Somebody's slower than char, but none are equal in speed
                self.participants[firstLess:firstLess] = [char]
                self.turn += 1 if firstLess <= self.turn else 0
            else: # There a tie in speed stats
                if firstLess == -1: # char is tied for slowest
                    firstLess = len(self.participants)
                ties = self.participants[firstEq:firstLess] # All the characters with the same speed as char
                index = randint(0, len(ties))
                ties[index:index] = [char] # Insert char at a random location within the ties
                self.participants[firstEq:firstLess] = ties # and put them back into participants
                self.turn += 1 if firstLess + index <= self.turn else 0
            char.pos = clampPosWithinField(char.pos, self.size)

    # No undefined behavior here
    def addParticipant(self, name):
        self.addParticipantByChar(self.characters[name.lower()])

    def removeParticipantByChar(self, char):
        index = self.participants.index(char)
        self.participants[index:index+1] = []
        if len(self.participants) == 0:
            self.turn = -1
        elif self.turn > index:
            self.turn -= 1

    def currentChar(self):
        if self.turn == -1:
            return self.participants[0]
        else:
            return self.participants[self.turn]

    def currentCharPretty(self):
        return 'It is ' + self.currentChar().name + "'s turn. " + self.participants[self.turn].username

    def __str__(self):
        out = self.name + ' (' + self.id + ')\n'
        out += 'Characters:\n'
        for k, v in self.characters.items():
            out += v.name + ' '
        if len(self.participants) > 0:
            out += '\n\nOrder of Initative [current HP]:\n'
            for char in self.participants:
                out += char.name + '[' + str(char.health) + '] '
            # out += '\n\nSorted by Location (current range):\n'
            # for char in sorted(self.participants, key=lambda char: char.location):
            #     out += char.name + '(' + str(char.location) + ') '
            out += '\n\n' + self.currentCharPretty()
            if self.turn == -1:
                out += "\n\nThe battle has yet to begin!"
        else:
            out += '\n\nThere is no active battle.'
        return out

    def delete(self, name):
        char = self.characters[name.lower()]
        char.clearModifiers()
        for m in char.ownedModifiers:
            m.revoke()
        del self.characters[name.lower()]
        try:
            self.removeParticipantByChar(char)
        except ValueError:
            pass

    def addOrphanModifier(self, mod):
        self.orphanModifiers.append(mod)

    def tickOrphanModifiers(self):
        for m in self.orphanModifiers:
            m.tick()

    def passTurn(self):
        self.currentChar().tickModifiers()
        self.moved = False
        self.attacked = False
        if self.turn == -1:
            self.turn = 1
        else:
            self.turn += 1
        if self.turn >= len(self.participants):
            self.turn = 0
            self.tickOrphanModifiers()

    def availableActions(self):
        if self.moved and self.attacked:
            return ''
        elif self.attacked:
            return '\n\nYou may use /move to move, or /pass to pass your turn.'
        elif self.moved:
            return '\n\nYou may use /attack to perform a basic physical attack, /ability to use an ability, or /pass to pass your turn.'
        else:
            return '\n\nYou may use /move and either /attack or /ability this turn, if you wish.'

    def basicAttack(self, targetName):
        if self.attacked:
            return self.availableActions()
        user = self.currentChar()
        target = self.characters[targetName.lower()]
        if target not in self.participants:
            return target.name + ' is not participating in the battle!'
        if distance(user.pos, target.pos) > BOXING_MAX:
            return target.name + ' is too far away!'
        out, damage = target.rollFullAttack(user.acc(), user.atk(), secret=user.secret)
        if target.health <= 0:
            self.removeParticipantByChar(target)
            target.respawn()
        self.attacked = True
        out += self.availableActions()
        if self.moved:
            self.passTurn()
        return out

    # Returns (step, restOfCodex). Just accounts for using a name as a waypoint. Other stuff will return (None, theWholeCodex), just like parseDirection().
    def parseStep(self, codex, curPos):
        step, codex = parseDirection(codex)
        if step is None:    # Current element of codex cannot be parsed as a direction because it is not formatted like '2W' or '5s'
            if codex[0].lower() in self.characters:     # If the element is the name of a character (case-insensitive)
                newPos = self.characters[codex[0].lower()].pos  # add a segment going straight to their position
                step = addVec(newPos, flipVec(curPos))
                codex = codex[1:]
        return step, codex

    # Syntax: /move [[distance]cardinal | name | + | - distTweak] ... [+ | maxDistance]
    # Return: (path, maxDist, stop), just like the parameters in Character.testMove()
    def parseDirectionList(self, startPos, codex):
        path = []
        pos = startPos
        while len(codex) > 0:
            step, codex = self.parseStep(codex, pos)
            if step is None:    # Current element of codex cannot be parsed as a direction because it is not formatted like '2W' or '5s'
                if len(codex) == 1: # Last element of codex may optionally use special syntax
                    try:
                        maxDist = int(codex[0])     # If the last element can be parsed as an integer, use it as the maximum distance
                        return path, maxDist, False
                    except ValueError:
                        if codex[0] == '+':     # Last element being a + sign means "keep going in this direction"
                            return path, -1, False
                elif codex[0] == '+':       # Add this step to the last one in the codex
                    codex = codex[1:]
                    nextStep, codex = self.parseStep(codex, pos)
                    if nextStep != None:
                        path[-1] = addVec(path[-1], nextStep)
                        pos = addVec(pos, nextStep)
                elif codex[0] == '-':   # Parse the next entry as an integer, and subtract it from the magnitude of the next step
                    codex = codex[1:]
                    try:
                        d = int(codex[0])
                        backStep = flipVec(setMag(path[-1], d))
                        path[-1] = addVec(path[-1], backStep)
                        pos = addVec(pos, backStep)
                        codex = codex[1:]
                    except ValueError:
                        raise ValueError('Expected an integer after - sign; got ' + codex[0])
                else:
                    raise ValueError('Could not parse direction or waypoint: ' + codex[0]) # If none of the above matched, raise an exception
            else:       # If an actual direction could be parsed
                path.append(step)
                pos = addVec(pos, step)
        return path, -1, True

    # def needAgilityRolls(self, theChar, newPos):
    #     pos = theChar.pos
    #     for k, char in self.characters.items():
    #         if char is not theChar:
    #             if char.canMelee(pos):
    #                 if not char.canMelee(newPos):
    #                     yield char

    def move(self, codex):
        if self.moved:
            return self.availableActions()
        curChar = self.currentChar()
        pos = curChar.pos
        path, maxDist, stop = self.parseDirectionList(pos, codex)
        out, newPos = curChar.testMove(path, maxDist, stop, self.size)
        # for char in self.needAgilityRolls(curChar, newPos):
        #     log, escape = prettyCheck(curChar.spd(), char.spd(), (curChar.secret, char.secret), aglCheckFlavors)
        #     out += '\n\nTrying to escape {:s}:\n'.format(char.name) + log
        #     if not escape:
        #         return out
        curChar.pos = newPos
        self.moved = True
        out += self.availableActions()
        if self.attacked:
            self.passTurn()
        return out

    def genMap(self, corner1, corner2, scale=1):
        minX = min(corner1[0], corner2[0])
        minY = min(corner1[1], corner2[1])
        maxX = max(corner1[0], corner2[0])# + 1
        maxY = max(corner1[1], corner2[1])# + 1
        theMap = []
        abbrevs = {}
        repeats = 0
        for y in range(maxY, minY - 1, -scale):
            row = []
            for x in range(minX, maxX + 1, scale):
                tile = '  '
                isNumericTile = False
                chars = []
                for char in self.participants:
                    if char.inBox(x - scale + 1, x, y, y + scale - 1):
                        chars.append(char.name)
                        if tile == '  ':
                            tile = '{:2s}'.format(char.name[0:2])
                        elif not isNumericTile:
                            tile = '{:02d}'.format(repeats)
                            isNumericTile = True
                            abbrevs[tile] = chars   # This makes abbrevs[tile] be a *reference* to chars, right? I hope?
                            repeats += 1
                row.append(tile)
            theMap.append(row)
        return theMap, abbrevs

    def formatMap(self, corner1, corner2, scale=1):
        theMap, abbrevs = self.genMap(corner1, corner2, scale)
        out = ''
        for k, v in sorted(abbrevs.items()):
            out += '{} = {!s}\n'.format(k, v)
        minX = min(corner1[0], corner2[0])
        minY = min(corner1[1], corner2[1])
        maxX = max(corner1[0], corner2[0])# + 1
        maxY = max(corner1[1], corner2[1])# + 1
        coords = ''
        for i in range(minX, maxX + scale * 2, scale * 2):
            coords += '{:02d}  '.format(i)[-4:]
        out += '\n`={}=`'.format(coords[:len(theMap[0]) * 2])
        for r in range(len(theMap)):
            out += '\n`|'
            for c in range(len(theMap[0])):
                out += theMap[r][c]
            out += '|`'
        return out



# All of the Battles known to Battlebot, with all their data, keyed by guild ID.
database = {}

def guildExists(guild):
    return guild.id in database

def createGuild(guild):
    if guildExists(guild):
        raise ValueError(guild.name + 'is already known to Battlebot!')
    else:
        database[guild.id] = Battle(guild)

def stats(codex):
    out = '`{:11s}  {:>5s} {:>5s} {:>5s} {:>5s} {:>5s} {:>5s}`\n'.format('Size Tier', 'HP', 'Acc', 'Eva', 'Atk', 'Def', 'Spd')
    ss = defaultStats(1);
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`\n'.format('1 (Faerie)', ss['HP'], ss['ACC'], ss['EVA'], ss['ATK'], ss['DEF'], ss['SPD'])
    ss = defaultStats(2);
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`\n'.format('2 (Werecat)', ss['HP'], ss['ACC'], ss['EVA'], ss['ATK'], ss['DEF'], ss['SPD'])
    ss = defaultStats(3);
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`'.format('3 (Kraken)', ss['HP'], ss['ACC'], ss['EVA'], ss['ATK'], ss['DEF'], ss['SPD'])
    return out

def makeChar(codex, author):
    char = Character(author, codex[0], codex[1].lower(), makeStatsFromCodex(codex[2:]))
    if not guildExists(author.server):
        createGuild(author.server)
    database[author.server.id].addCharacter(char)
    return str(char) + '\n\n{:d} stat points used.'.format(sum(char.statPoints.values()))

def clearBattle(codex, author):
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        database[author.server.id].clear()
        return 'Battle data cleared.'
    else:
        return "You need Manage Messages or Administrator permission to clear the battle state!"

def joinBattle(codex, author):
    battle = database[author.server.id]
    battle.addParticipant(codex[0])
    return codex[0] + ' has successfully joined the battle!'

def battleStatus(codex, author):
    battle = database[author.server.id]
    return str(battle)

def charData(codex, author):
    battle = database[author.server.id]
    return str(battle.characters[codex[0].lower()])

def info(codex, author):
    if len(codex) == 0:
        return battleStatus(codex, author)
    else:
        return charData(codex, author)

def modifiers(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    mods = char.listModifiers()
    if len(mods) > 0:
        return mods
    else:
        return char.name + ' has no modifiers.'

def deleteChar(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        battle.delete(codex[0])
        return codex[0] + ' was successfully deleted.'
    else:
        return "You need Manage Messages or Administrator permission to delete other players' characters!"

def passTurn(codex, author):
    battle = database[author.server.id]
    char = battle.currentChar()
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        battle.passTurn()
        return 'Turn passed successfully.\n\n' + battle.currentCharPretty()
    else:
        return "You need Manage Messages or Administrator permission to take control of players' characters!"

def basicAttack(codex, author):
    battle = database[author.server.id]
    char = battle.currentChar()
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return battle.basicAttack(codex[0]) + '\n\n' + battle.currentCharPretty()
    else:
       return "You need Manage Messages or Administrator permission to take control of players' characters!"

def move(codex, author):
    battle = database[author.server.id]
    char = battle.currentChar()
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return battle.move(codex) + '\n\n' + battle.currentCharPretty()
    else:
       return "You need Manage Messages or Administrator permission to take control of players' characters!"

# /map
# /map scale
# /map centerX centerY
# /map centerX canterY radius
# /map x1 x2 y1 y2
# /map x1 x2 y1 y2 scale
def showMap(codex, author):
    battle = database[author.server.id]
    out = ''
    if len(codex) == 0:
        size = max(battle.size)
        scale = math.ceil(size / 26)
        out =  battle.formatMap((0, 0), addVec(battle.size, (-1, -1)), scale)
    elif len(codex) == 1:
        out = battle.formatMap((0, 0), addVec(battle.size, (-1, -1)), int(codex[0]))
    elif len(codex) == 2:
        center = (int(codex[0]), int(codex[1]))
        corner1 = clampPosWithinField(addVec(center, (-13, -13)), battle.size)
        corner2 = clampPosWithinField(addVec(center, (13, 13)), battle.size)
        out = battle.formatMap(corner1, corner2, 1)
    elif len(codex) == 3:
        center = (int(codex[0]), int(codex[1]))
        radius = int(codex[2])
        corner1 = clampPosWithinField(addVec(center, (-radius, -radius)), battle.size)
        corner2 = clampPosWithinField(addVec(center, (radius, radius)), battle.size)
        out = battle.formatMap(corner1, corner2, 1)
    elif len(codex) == 4:
        corner1 = clampPosWithinField((int(codex[0]), int(codex[2])), battle.size)
        corner2 = clampPosWithinField((int(codex[1]), int(codex[3])), battle.size)
        out = battle.formatMap(corner1, corner2, 1)
    else:
        corner1 = clampPosWithinField((int(codex[0]), int(codex[2])), battle.size)
        corner2 = clampPosWithinField((int(codex[1]), int(codex[3])), battle.size)
        out = battle.formatMap(corner1, corner2, int(codex[4]))
    if len(out) >= 2000:
        return 'Map too large. Try decreasing the size or increasing the scale factor.'
    else:
        return out

def restat(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        if char not in battle.participants:
            char.statPoints = makeStatsFromCodex(codex[1:])
            return str(char) + '\n\n{:d} stat points used.'.format(sum(char.statPoints.values()))
        return "You need Manage Messages or Administrator permission to restat your character during a battle!"
    else:
        return "You need Manage Messages or Administrator permission to restat other players' characters!"

# Formatted like +10% STR 5
def parseModifier(codex):
    dur = codex[2]
    if dur[0] == '(':       # Remove parens if present
        dur = dur[1:]
    if dur[-1] == ')':
        dur = dur[:-1]
    dur = int(dur)
    stat = codex[1].upper()
    factor = codex[0]
    if factor[-1] == '%':
        factor = factor[:-1]
        isMult = True
        if factor[0] == '+':
            factor = int(factor[1:])
            factor = 1 + factor / 100
        elif factor[0] == '-':
            factor = int(factor[1:])
            factor = 1 - factor / 100
        else:
            factor = int(factor) / 100
    else:
        isMult = False
        factor = int(factor)
    return (stat, factor, dur, isMult)

def addModifier(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        try:
            owner = battle.characters[codex[-1].lower()]
        except KeyError:
            owner = None
        mod = Modifier(parseModifier(codex[1:]), holder=char, owner=owner) # Will automatically attach itself to the correct characters
        if owner is None:
            battle.addOrphanModifier(mod)
        return char.listModifiers()
    else:
        return "You need Manage Messages or Administrator permission to create modifiers!"

def warp(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        char.pos = int(codex[1]), int(codex[2])
        return str(char)
    else:
        return "You need Manage Messages or Administrator permission to teleport characters!"

def setHealth(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        if len(codex) > 1:
            char.health = int(codex[1])
        else:
            char.respawn()
        return str(char)
    else:
        return "You need Manage Messages or Administrator permission to set characters' HP!"

def toggleSecret(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        char.secret = not char.secret
        return str(char)
    else:
        return "You need Manage Messages or Administrator permission to change characters' visibility!"

def gm_attack(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        acc = int(codex[1])
        atk = int(codex[2])
        secret = len(codex) > 3
        if atk <= 0:
            return char.rollCheck(acc, secret=secret)[0]
        elif acc <= 0:
            return char.rollDamage(atk, secret=secret)[0]
        else:
            return char.rollFullAttack(acc, atk, secret=secret)[0]
    else:
        return "You need Manage Messages or Administrator permission to perform GM attacks!"

##################################################
##### Bot boilerplate code exists below here #####
##################################################

def get_invite(idnum):
    return "https://discordapp.com/oauth2/authorize?client_id=" + str(idnum) + "&scope=bot&permissions=0"


handler = logging.FileHandler(filename='battlebot.log', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

client = discord.Client()

@client.event
async def on_ready():
    print('Timestamp: ' + str(datetime.now()))
    print('Discord API: ' + str(discord.__version__))
    print('Bot Name: ' + str(client.user.name))
    print('Bot ID: ' + str(client.user.id))
    print('Invite Link: ' + get_invite(client.user.id))

help_dict = {'bot': """Welcome to BattleBot!
This is a Discord bot written by Someone Else 37 using discord.py.
It rolls dice and things, and has a multitude of commands useful for anyone GMing a role-play using the
combat system lenscas and I developed for ANWA. It is based off the combat system used in BtNS and ABG.
In fact, BattleBot can just about handle all of the mechanics of an ANWA RP on its own. Just add flavor.
Or, at least, it will once it's complete. Battlebot is a work in progress.

Battlebot kind of grew out of an simple dicebot written by Eruantien. Much thanks to him for getting me started.

For more info on how to use BattleBot, type /help contents

Want to add BattleBot to your server? Type /invite
\*Note, this may not actually give you a functional invite link. I'm not sure why.

Want to host BattleBot yourself, look at the sourcecode, or file a bug report? Type /github""",
        'contents': """Table of Contents

/help bot: General bot information
/help contents: View this page again
/help player: Useful commands for players in an RP
/help battle: Commands for use during a battle
/help move: Detailed information on the /move command
/help move2: /move, page 2
/help map: Detailed information on the /map command
/help stats: How stats work in BattleBot
/help modifier: How stat modifiers (i.e. buffs and debuffs) work
/help ability: Deailed information on abilities and how to create them (coming soon!)
/help rpn: Crash course on Reverse Polish Notation
/help rpn2: Details on BattleBot's take on RPN
/help rpn3: RPN operators only useful in abilities
/help gm: Commands for GMs
/help calc: Commands that roll dice and calculate stuff. Mostly obsoleted by all the above.

**Do Note:** Many of these help pages are quite long. Please do not use them outside of your server's designated spam channel, or the GM (and the other players) will be very annoyed with you.""",
        'player': """Player Commands
These commands are usable by all players, and do not typically have any impact on the state of the battle.

/roll XdY: Roll X dYs and add the results.
/defaultstats: Print out the default stats for all the size tiers.
/makechar name race [hp acc eva atk dfn spd]: Create a character with the given name, race, and stat point distribution.
    Accepted races: faerie, elf, human, werecat, elfcat, cyborg, robot, kraken, elfship, steamship
/restat name hp acc eva atk dfn spd: Reshuffle your stats. Only works outside of battle.
/delete name: Delete a character. Only works on characters you created. Warning, this is permanent!
/join name: Join the battle ongoing on your server.
    Support for using /join with no argument to automatically add one of your characters is planned, but NYI.
/list: List a bunch of info about the current state of the battle- who's participating, turn order, etc.
/list name: Show all the info about the named character.
/modifiers name: Show all modifiers on the named character.
/invite: Show BattleBot's invite link.
/github: Show the link to this bot's sourcecode on GitHub.""",
        'battle': """Battle Commands
These commands are to be used during battle, and can only be used by the active player or a GM. See /help gm for more info.

/attack name: Punch the named character with a basic physical attack.
    This and the next few commands only work during your turn.
/move ...: Move along the specified path, as far as your speed roll allows.
    See /help move for info on the path syntax.
/ability ...: Use an ability. Not yet implemented, but coming soon!
/pass: Pass your turn. Simple enough.

Note: During their turn, the active player may use both /move AND either /attack or /ability, if they wish (although they cannot use /attack and /ability in the same turn).""",
        'move': """The /move Command
This command allows players to move about the battlefield. Its syntax is quite flexible and powerful, if a bit complex.

The simplest way to use /move is to simply give it a pair of NS/WE coordinates. Example:
/move 5N 3E
will move the character along a straight line to a point at most 5 units north and 3 units east of their current position.
Henceforth, I will call this bit of syntax a "direction". The coordinates can be specified in any order, and lowercase letters work fine.
You can even leave out the NS or WE coordinate entirely. /move 3s means "go 3 units due south".
Furthermore, if you leave out the distance component, it will default to 1. /move N means "go one tile north".

Alternatively, you can type out the name of any character in the battle in place of coordinates, and BattleBot
will interpret that as "go straight toward the location of the named character." It's actually treated as a
direction internally, and I will use that term interchangably to refer to both.

Type /help move2 to continue reading""",
        'move2': """The full argument format of /move is this:
/move direction [direction | + direction | - dist] ... [+ | dist]
Remember, you can use names as waypoints in place of directions.
Essentially, it takes a list of directions (and waypoints), and the character will follow that path as far as the speed roll permits.

Placing a + sign between two directions will cause them to be added together, and the character will perform both at once by traveling a straight line. Example:
/move lenscas + 2E
will be interpreted as "go two tiles to the east of lenscas".

Following a direction by a - sign, then an integer distance, will cause the character to stop short of where the previous direction command would've taken them, by no more than the specified distance in tiles. If you've got an ability with a maximum range of 16, for instance, you can type
/move lenscas - 16
to move just within range.

The list of directions can also be suffixed with either a + sign or an integral distance.
/move 2N 1S 5E +
means "move 2 tiles north, then in the direction of 1S 5E, and keep going in that direction as far as the speed roll permits."

If the last argument is an integer, it means "move no more than this many tiles, continuing past the end of the path in the direction of the last segment if necessary."
/move N E 25
will be interpreted as "move northeast as far as possible, up to 25 tiles." """,
        'map': """The /map Command

/map, well, draws a map of the battlefield. It, too, is very flexible, though not nearly as complex as /move.
The default size of the map is 26x26. This nicely fits within a Discord post.

/map: if given no arguments, map the entire battlefield, scaled to fit within a single post.
/map scale: draw the whole battlefield, using the specified scale factor. Bigger numbers yield a smaller, more zoomed-out map.
/map x y: draw a map of the default size centered on the given location, with scale factor 1 (i.e. 1 map tile = 1 grid tile)
/map x y radius: draw a map of the given size centered on the given point, with scale factor 1.
/map xMin xMax yMin yMax: draw a map covering the given area
/map xMin xMax yMin yMax scale: draw a map covering the given area, with the given scale factor. Again, bigger scale factor = more zoomed-out map.

The map will show characters with the first two letters in their name. If two characters exist in the same tile, BattleBot will use a number instead and display a legend showing who all is represented by each number.

I plan to have /map automatically give a view of the most interesting area of the battlefield eventually, but I'm not quite entirely sure how to do that. Any ideas?""",
        'stats': """Stats and How They Work

Battlebot's stat system is a bit complex, so I thought I ought to explain it here.

Each race is given a set of default stats. Currently, these depend solely on the size tier of the species, but if Lens wishes, I can give each species its own default stats quite easily. Just say the word.
Type /calc defaultstats to see what these size-based stats are.

Anyhow, each player character is given a set number of stat points, as mandated by the GM, to distribute among the six stats as they wish. Each point allocated to a stat increases it by *one eighth of the stat's default value*.

For instance, werecats have 16 base HP. A werecat with 0 points allocated to HP will have, well, 16 HP. No points allocated = no change in the stat.
A werecat with one point in HP will have 16 + (1 * 16 / 8) = 18 HP.
A werecat with 4 points in HP will have 16 + (4 * 16 / 8) = 24 HP.

Allocating 4 points will multiply the default stat by 1.5, and allocating 8 points will double it. It's pretty linear.

What are these stats, you ask? Well.
HP: Health points. Basically how much damage you can take before you die.
ACC: Accuracy. The more of this you have, the more likely you'll actually be able to land an attack.
EVA: Evasion. The more of this you have, the better your chances of dodging an attack and taking no damage at all.
ATK: Attack. How hard you hit.
DEF: Defense. How well you are able to resist being hit.
SPD: Speed. Determines order of initiative and how quickly you can move around the battlefield.""",
        'modifier': """Modifiers

Battlebot supports modifiers to stats, of the multiplicative and additive varieties. The multiplicative ones apply first.
Each modifier has the following data:
    Stat: Which stat the modifier, well, modifies.
    Strength: The amount by which the modifier modifies its associated stat.
    Duration: How long the modifier will last.
    Holder: The character to which the modifier applies.
    Owner: The character who created the modifier.

The durations of all modifiers tick down at the end of the turn of their *owner*. When the modifier's duration drops below zero, it is removed entirely.
Thus, a modifier with duration 0 will vanish at the end of its creator's next turn (or current turn, if it is currently their turn).
A newly-created modifier with duration N is guaranteed to last exactly N full turn cycles, barring ability shenenigans.

Also note that modifiers whose durations are already negative will never decay. They are only cleared at the end of a battle (again, barring ability shenanigans).

Also, modifiers instantly vanish the moment their owner dies. Because otherwise, modifiers whose creators died would never expire, and that would be weird.
Unless they have no owner, which is also possible to do.
""",
        'ability': """**Not Yet Implemented**""",
        'rpn': """Reverse Polish Notation

RPN is a way to write mathematical formulae and such. It will seem a bit strange to anyone used to the familiar infix notation, but is very easy for computers to understand.
RPN is a *postfix* notation, meaning that all operators come *after* the things they operate on. For example:
/calc rpn 2 3 4 + 5 - *
The interpreter will read this string with the help of a stack. Whenever it encounters a number, it will push that number onto the stack. After reading the 2, the stack will look like this:
`[2]`
Then, after the 3 and 4 are read:
`[2, 3, 4]`
Note that I'm showing the top of the stack as the rightmost end of this list.
Most operators, including + and *, will pop *two* values off the stack, operate on them, and push the result back onto the stack.
Upon reading the + sign, the interpreter will pop the 4 and 3 off the stack, add them to get 7, and push the 7 back onto the stack. The stack now looks like this:
`[2, 7]`
Next comes the 5.
`[2, 7, 5]`
The - sign will pop the 5 and 7. 7-5=2:
`[2, 2]`
And, finally, * will multiply the 2s.
`[4]`
The input has been exhausted, and the stack has only one element. That whole formula thus evaluates to 4.
And indeed, 2 * ((3 + 4) - 5) = 4.

RPN allows math formulae to be written in a perfectly unambiguous manner that is very easy to parse. It's quite nice.

Type /help rpn2 for more details on exactly what operations BattleBot's RPN parser can perform.""",
        'rpn2': """BattleBot RPN

BattleBot's RPN parser has a number of operations that it can perform. First, the basics. These operators all pop two numbers off the stack, and push their result back on.
+ : Addition. Pretty simple.
- : Subtraction. Note that the second number popped is the number the other is subtracted *from*- so "5 1 -" means the same thing as "5 - 1" equals 4. Not -4.
        All the operators that take multiple arguments work this way. The first number pushed goes on the left hand side of the operator.
* : Multiplies the two numbers. Simple.
/ : Floor division. Divides, then rounds down (i.e. toward -infinity). "5 2 /" evaluates to 2.

The rest of these have English names, and are not case-sensitive.
sum: Add together ALL the numbers on the stack, and push the result back on as the only element in the stack.
        So "1 2 3 4 5 sum" returns 15.

roll: Takes one argument off the stack. Roll that namy d10s, and push the sum back on the stack.
rollh: Like roll, except hide the individual rolls. Just return the sum.
rollu: As above, but hide the rolls if the user's stats are secret.
rollt: As above, but look at the target's secret status.
rollacc: Perform an accuracy check. Take two arguments and roll that many d10s.
calcdmg: If the two arguments are 50 and 20, return how much damage would be dealt if I rolled a 50 and you rolled a 20.
rolldmg: Roll the two arguments, then call calcdmg on the results.

All of the above commands are available to /calc rpn, so try them out yourself.
For the RPN commands that really only make sense in the context of an ability, type /help rpn3.""",
        'rpn3': """RPN Ability Commands

First off, you should be aware that the RPN parser can handle several different types of values. Integers are parsed as, well, integers; anything that doesn't parse as an integer or match any of the operators will be parsed as a string; and some of the operators can return more complex objects.

These first few aren't operators, per se, as they take no arguments at all.
self: The actual Character using this ability. Intended to be followed by one of the commands in the next section.
target: The character targeted by this ability.
locus: For an AOE ability, the location where the effect is centered. Not available otherwise.

These all take one argument, extected to be a character (so... self or target).
hp: The *maximum* HP of the character.
acc: The Accuracy stat of the character. All modifiers and whatnot are properly taken into account.
eva: Evasion stat.
atk: Attack.
def: Defense.
spd: Speed.
health: The character's *current* HP.
pos: The character's position.

Next, the modifier operators. All take three arguments, of the form [factor, stat, duration]. They do not affect anything right away, but the returned object can be applied to a character later on in the ability.
They are +mod, -mod, mod%, +mod%, and -mod%. The syntax parallels that of /addModifier, described in /help gm. So I'll just give some examples in the RPN format here:
    10 STR 3 +mod == +10 Strength for 3 turns
    5 EVA 2 -mod == -5 Evasion for 2 turns
    150 SPD 0 mod% == 150% Speed until end of turn
    20 DEF 1 +mod% == +20% (== 120%) Defense for 1 turn
    15 ACC -1 -mod% == -15% (== 85%) Accuracy until end of battle

And finally, with two arguments,
dist: The Pythagorean straight-line distance between two locations (as returned by locus or pos). May be used to have the effect of an ability depend on the distance between the user and the target, or on the distance between the target and the epicenter of an AOE effect, etc. Go wild.""",
        'gm': """GM commands
These commands/behaviors only function if you are a GM, meaning that you have either Administrator or Manage Messages permission on the server.

/pass, /attack, /delete, etc: GMs can use these commands to control or mess with other players' characters.
    GMs can also /restat characters that are currently partaking in a battle.
/clear: Clear the current battle and heal and respawn all participants.
/addModifier name [+|-]factor[%] stat duration [owner]: Added a modifier to the named character.
    If the % is omitted, create an additive multiplier that increases the stat by the specified amount (or dereases it, if negative).
    If the % is present. what happens depends on the sign given, if any.
        Plus sign means "increase this stat by the specified pecentage"
        Minus sign means "decrease this stat by the specified percentage"
        No sign means "set this stat to this percentage of what is was before"
    So 120% and +20% mean the same thing, as do 80% and -20%.
    Acceptable stats are HP, ACC, EVA, STR, DEF, and SPD. All are case-insensitive.
/warp name x y: Teleports the named character to the given coordinates.
/sethp name [health]: Sets the named character's current health, or to their maximum health is none is specified.
/togglesecret name: Toggle whether the named character's stats are hidden from players.
/gmattack name acc atk [secret?]: Perform at attack with the given Accuracy and Attack against the named character.
    If 0 or a negative number is specified for acc or atk, those stats will not be rolled.
    If anything at all is given for the fourth parameter, the bot will not echo the Accuracy or Attack specified.
    It's up to you to delete/edit your post to prevent players from reading the stats from it.""",
        'calc': """Calculation Commands
These just roll dice and calculate stuff. They have no effect on the battle at all.

/calc roll XdY: Roll X dYs and add the results. Alias of /roll.
/calc check acc eva: Roll a BtNS-style accuracy check.
/calc damage atk def: Do a damage roll in my fancy BtNS-inspired way.
/calc avgdmg atk def: Do 1000 damage rolls, calculate a bunch of summary statistics, and produce a histogram.
   Each `#` in the histogram represents 10 rolls that dealt that amount of damage, `|` is 5, `:` is 2, and `.` is 1
/calc attack acc atk eva def hp: Roll accuracy and damage repeatedly, until HP damage has been dealt.
/calc repattack acc atk eva def hp: Run /attack many times over, then return summary statistics and a histogram.
/calc range r: Convert a range integer into a human-readable string.
/calc rangedump: Generate a list of all the range ranges, and their names.
/calc rangelookup strn: Look up the given range string, and return the range integers that it corresponds to.
    Only requires that the given name be a substring of the name in BattleBot's sourcecode, and ignores case:
    /calc rangelookup ortBOW works fine.
/calc approach r spd [r2]: Do an approach roll, approaching the melee circle or, optionally, another character at range r2.
/calc retreat r spd: Do a retreat roll.
/calc defaultstats: Print out the default stats for all the size tiers. Alias of /defaultstats.
/calc testStatRoll n bucketSize: Test my new statical dice-rolling code against the count-and-add code by rolling n d10s.
    Returns a histogram. Each row is a bucket of bucketSize, collecting all rolls from one algorithm within its range.
    The even-numbered rows correspond to the count-and-add algorithm; the odd ones to the new statistical algorithm.
/calc rpn ...: Invoke BattleBot's RPN parser. Type /help rpn for more info."""}

git_link = 'https://github.com/SomeoneElse37/BattleBot'

PREFIX = '/'

def getReply(content, message):
    if content.startswith(PREFIX):
        codex = content[len(PREFIX):].split(' ');
        if codex[0] == 'calc':
            codex = codex[1:]
            if codex[0] == 'roll':
                return roll(codex[1:])
            elif codex[0] == 'check':
                return check(codex[1:])
            elif codex[0] == 'damage':
                return damage(codex[1:])
            elif codex[0] == 'avgdmg':
                return averagedamage(codex[1:])
            elif codex[0] == 'attack':
                return attack(codex[1:])
            elif codex[0] == 'repattack':
                return repattack(codex[1:])
            elif codex[0] == 'repatk':
                return repattack(codex[1:])
            elif codex[0] == 'range':
                return checkrange(codex[1:])
            elif codex[0] == 'rangedump':
                return rangedump()
            elif codex[0] == 'rangelookup':
                return checkRangeReverse(codex[1:])
            elif codex[0] == 'approach':
                return calcApproach(codex[1:])
            elif codex[0] == 'retreat':
                return calcRetreat(codex[1:])
            elif codex[0] == 'defaultstats':
                return stats(codex[1:])
            elif codex[0] == 'testStatRoll':
                return testStatisticRolls(codex[1:])
            elif codex[0] == 'rpn':
                return testRPN(codex[1:])
        elif codex[0] == 'help':
            if len(codex) > 1:
                key = codex[1].lower()
                if key in help_dict:
                    return help_dict[key]
            else:
                return help_dict['bot']
        elif codex[0] == 'roll':
            return roll(codex[1:])
        elif codex[0] == 'defaultstats':
            return stats(codex[1:])
        elif codex[0] == 'makechar':
            return makeChar(codex[1:], message.author)
        elif codex[0] == 'restat':
            return restat(codex[1:], message.author)
        elif codex[0] == 'join':
            return joinBattle(codex[1:], message.author)
        elif codex[0] == 'list':
            return info(codex[1:], message.author)
        elif codex[0] == 'modifiers':
            return modifiers(codex[1:], message.author)
        elif codex[0] == 'attack':
            return basicAttack(codex[1:], message.author)
        elif codex[0] == 'pass':
            return passTurn(codex[1:], message.author)
        elif codex[0] == 'move':
            return move(codex[1:], message.author)
        elif codex[0] == 'map':
            return showMap(codex[1:], message.author)
        elif codex[0] == 'clear':
            return clearBattle(codex[1:], message.author)
        elif codex[0] == 'delete':
            return deleteChar(codex[1:], message.author)
        elif codex[0] == 'addModifier':
            return addModifier(codex[1:], message.author)
        elif codex[0] == 'warp':
            return warp(codex[1:], message.author)
        elif codex[0] == 'sethp':
            return setHealth(codex[1:], message.author)
        elif codex[0] == 'togglesecret':
            return toggleSecret(codex[1:], message.author)
        elif codex[0] == 'gmattack':
            return gm_attack(codex[1:], message.author)
        elif codex[0] == 'github':
            return git_link
        elif codex[0] == 'invite':
            return get_invite(client.user.id)
    return ""

@client.event
async def on_message(message):
    try:
        reply = getReply(message.content, message)
        if(len(reply) != 0):
            await client.send_message(message.channel, reply)
    except Exception as err:
        await client.send_message(message.channel, "`" + traceback.format_exc() + "`")

CURRENT_DB_VERSION = 10

def updateDBFormat():
    if 'version' not in database or database['version'] < CURRENT_DB_VERSION:
        print("Updating database format.")
        database['version'] = CURRENT_DB_VERSION
        for k, v in database.items():
            if k != 'version':
                # Battle attributes: characters, participants, turn, id, name, radius
                if not hasattr(v, 'size'):
                    v.size = (1024, 1024)
                    delattr(v, 'radius')
                if not hasattr(v, 'moved'):
                    v.moved = False
                if not hasattr(v, 'attacked'):
                    v.attacked = False
                if not hasattr(v, 'orphanModifiers'):
                    v.orphanModifiers = []
                for l, w in v.characters.items():
                    # Character attributes: username, userid, name, race, size, statPoints, baseStats, abilities, modifiers, health, location, secret
                    if not hasattr(w, 'statPoints'):
                        w.baseStats = baseStats[w.race]
                        w.statPoints = {}
                        if hasattr(w, 'stats'):
                            for n, s in w.stats.items():
                                # stat = base + base/8 * points
                                # stat - base = base/8 * points
                                # 8(stat - base) = base * points
                                # 8(stat - base) / base = points
                                # points = 8(stat - base) / base
                                # points = 8 * (stat - base)/base
                                # points = 8 * (stat/base - base/base)
                                # points = 8 * (stat/base - 1)
                                w.statPoints[n] = int(8 * (w.stats[n]/w.baseStats[n] - 1))
                        delattr(w, 'stats')
                    if not hasattr(w, 'abilities'):
                        w.abilities = []
                    if not hasattr(w, 'modifiers'):
                        w.modifiers = []
                    if not hasattr(w, 'location'):
                        w.location = 0
                    if not hasattr(w, 'secret'):
                        w.secret = False
                    if not hasattr(w, 'pos'):
                        w.pos = (0, 0)
                        delattr(w, 'location')
                    if hasattr(w, 'moved'):
                        delattr(w, 'moved')
                    if hasattr(w, 'attacked'):
                        delattr(w, 'attacked')
                    if hasattr(w, 'abilities'):
                        delattr(w, 'abilities')
                    if not hasattr(w, 'modifiers'):
                        w.clearModifiers()
                    if hasattr(w, 'orphanModifiers'):
                        delattr(w, 'orphanModifiers')
                    if not hasattr(w, 'ownedModifiers'):
                        w.ownedModifiers = []
        ##### This is where CHARACTER attributes get added! BATTLE attributes go above and an indent level to the left! Stop forgetting that, SE!


token = ''

datafile = 'battlebot.pickle'
dev_datafile = 'battlebot_dev.pickle'

if len(argv) > 1 and argv[1] == 'dev':
    print('Battlebot running in dev mode.')
    with open('devbot.token', mode='r') as f:
        token = f.readline().strip()
    datafile = dev_datafile
else:
    print('Battlebot running in release mode.')
    with open('bot.token', mode='r') as f:
        token = f.readline().strip()

try:
    with open(datafile, 'rb') as f:
        database = pickle.load(f)
    updateDBFormat()
    print(str(len(database) - 1) + ' guilds loaded.')
except FileNotFoundError:
    print('Database could not be loaded. Creating an empty database.')

try:
    client.run(token)  # Blocking call; execution will not continue until client.run() returns
finally:
    with open(datafile, 'wb') as f:
        pickle.dump(database, f, pickle.HIGHEST_PROTOCOL)
    print('Database saved to disk.')

#client.connect()



