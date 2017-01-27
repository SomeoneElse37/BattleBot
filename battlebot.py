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
from random import randint, gauss, shuffle

from statistics import *
from datetime import *
#Load the custom classes
from characters import *
from battles import *
from modifiers import *
from abilities import *

generateExcel = True
if generateExcel:
    try:
        import odsify_characters
        import os
    except ImportError:
        generateExcel=False
        print("Could not load odfpy. /excel is turned off")

def createExcel(characterList):
    if not generateExcel:
        return {'error':True,'message':"This command is not enabled right now"}
    else:
        pathToExcel = odsify_characters.generateODSFromCharacters(characterList)
        # with open(pathToExcel, 'rb') as f:
        #    await client.send_file(channel, f)
        return {'error':False,'file':pathToExcel,'message':"",'deleteAfterUpload':True}

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
        if n <= 100:
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
    dmg = max(math.ceil(ratio - 1), 0)
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



##################################################
##### Code for moderated battles begins here #####
##################################################





def makeStatsFromCodex(codex):
    if len(codex) >= 6:
        return makeStatDict(int(codex[0]), int(codex[1]), int(codex[2]), int(codex[3]), int(codex[4]), int(codex[5]))
    else:
        return makeStatDict(0, 0, 0, 0, 0, 0)



# I can use objects instantiated from a class that hasn't been defined yet, as long as I don't explicitly refer to that class, right?


def sumThings(xs, data):
    total = sum(xs)
    return [total], '{:d} = {!s}'.format(total, xs)

def flip(pair):
    a, b = pair
    return [b], a

def rollAccCheckForRPN(xs, data):
    log, hit = prettyCheck(xs[0], xs[1], data['secrets'])
    return [(1 if hit else 0)], log

# Any data that parseRPN() could be expected to be able to look up from the beginning
# By default, considers both "characters'" stats to be visible (because they don't really have stats to hide)
baseData = {'secrets': (False, False)}

# Operators and functions that parseRPN should have access to, even without any character context
baseFunctions = {'+': (2, lambda xs, data: ([xs[0] + xs[1]], '')),
        '-': (2, lambda xs, data: ([xs[0] - xs[1]], '')),
        '*': (2, lambda xs, data: ([xs[0] * xs[1]], '')),
        '/': (2, lambda xs, data: ([xs[0] / xs[1]], '')),
        '//': (2, lambda xs, data: ([int(xs[0] // xs[1])], '')),
        'sum': (-1, sumThings),
        'roll': (1, lambda xs, data: flip(prettyRoll(xs[0]))),                          # Rolls some d10s. Simple enough.
        'rollh': (1, lambda xs, data: flip(prettyRoll(xs[0], True))),                   # Rolls some d10s, but hides the actual rolls.
        'rollu': (1, lambda xs, data: flip(prettyRoll(xs[0], data['secrets'][0]))),     # Hides the actual rolls if and only if the user's stats are hidden.
        'rollt': (1, lambda xs, data: flip(prettyRoll(xs[0], data['secrets'][1]))),     # Hides the actual rolls if and only if the target's stats are hidden.
        'rollacc': (2, rollAccCheckForRPN),
        'calcdmg': (2, lambda xs, data: flip(damageString(xs[0], xs[1]))),
        'rolldmg': (2, lambda xs, data: flip(prettyDamage(xs[0], xs[1], data['secrets'])))}

# Parses an RPN codex, with the specified context. data and functions will be merged with baseData and baseFunctions,
# with the data and functions having precedence if any of the keys conflict.
def parseRPN(codex, data = {}, functions = {}):
    codex = [s.lower() for s in codex]
    data = {**baseData, **data}
    functions = {**baseFunctions, **functions}
    stack = []
    log = ''
    try:
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
                    retvals, note = fn(par, data)
                    stack.extend(retvals)
                    if len(note) > 0:
                        log += '\n' + note
                else:
                    log += '\nUnrecognized operator:' + op
    except (IndexError, TypeError) as e:
        raise RuntimeError('There was an error!', e, log, stack)
    if len(stack) == 1:
        return stack[0], log
    else:
        raise ValueError('Expected stack to contain exactly one item after execution; got ' + str(stack))

def testRPN(codex):
    retval, log = parseRPN(codex)
    return log + '\n\n' + str(retval)

# Used in the auxFunctions list to get a stat from an object, and format the result as parseRPN expects.
# Unless the object isn't a character, in which case just return the object and the stat.
# This would be so much easier in Haskell, where I don't need to go so far out of my way to curry functions with if statements in them...
def getstat(stat, alt, xs):
    try:
        return [getattr(xs[0], alt)()]
    except AttributeError:
        return [xs[0], stat]

def statgetter(stat, alt=None):
    if alt is None:
        alt = stat
    return lambda xs, data: (getstat(stat, alt, xs), '')

# These functions are formatted the same way as baseFunctions, but are aimed for use in abilities.
auxFunctions = {
        'hp':  (1, statgetter('hp')),
        'acc': (1, statgetter('acc')),
        'eva': (1, statgetter('eva')),
        'atk': (1, statgetter('atk')),
        'def': (1, statgetter('def', 'dfn')),
        'spd': (1, statgetter('spd')),
        'health': (1, lambda xs, data: ([xs[0].health], '')),
        'pos': (1, lambda xs, data: ([xs[0].pos], '')),
        'dist': (2, lambda xs, data: ([distance(xs[0], xs[1])], '')),
        '+mod': (3, lambda xs, data: ([(xs[2], xs[0], xs[1], False)], '')),
        '-mod': (3, lambda xs, data: ([(xs[2], -xs[0], xs[1], False)], '')),
        'mod%': (3, lambda xs, data: ([(xs[2], xs[0] / 100, xs[1], True)], '')),
        '+mod%': (3, lambda xs, data: ([(xs[2], 1 + xs[0] / 100, xs[1], True)], '')),
        '-mod%': (3, lambda xs, data: ([(xs[2], 1 - xs[0] / 100, xs[1], True)], ''))}
# stat, factor, duration, isMult
comparisons = {
        '<0': lambda n: n < 0,
        '==0': lambda n: n == 0,
        '>0': lambda n: n > 0,
        '<=0': lambda n: n <= 0,
        '!=0': lambda n: n != 0,
        '>=0': lambda n: n >= 0}

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
    char = battle.characters[codex[0].lower()]
    if char.userid == author.id:
        char.username = author.display_name
    return str(char)

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
        return "You need Manage Messages or Administrator permission to take control of other players' characters!"

def basicAttack(codex, author):
    battle = database[author.server.id]
    char = battle.currentChar()
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return battle.basicAttack(codex[0]) + '\n\n' + battle.currentCharPretty()
    else:
        return "You need Manage Messages or Administrator permission to take control of other players' characters!"

def move(codex, author):
    battle = database[author.server.id]
    char = battle.currentChar()
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return battle.move(codex) + '\n\n' + battle.currentCharPretty()
    else:
        return "You need Manage Messages or Administrator permission to take control of other players' characters!"

# Use an ability.
def useAbility(codex, author):
    battle = database[author.server.id]
    char = battle.currentChar()
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return battle.useAbility(codex) + '\n\n' + battle.currentCharPretty()
    else:
        return "You need Manage Messages or Administrator permission to take control of other players' characters!"

def createAbility(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    isGM = author.server_permissions.administrator or author.server_permissions.manage_messages
    if author.id == char.userid or isGM:
        if char not in battle.participants or isGM:
            try:
                abl = char.abilities[codex[1].lower()]
                abl.setFields(codex[2:])
                return str(abl)
            except KeyError:
                abl = Ability(codex[1:])
                char.abilities[abl.name.lower()] = abl
                return str(abl)
        else:
            return "You need Manage Messages or Administrator permission to modify characters during a battle!"
    else:
        return "You need Manage Messages or Administrator permission to modify other players' characters!"

def editAbility(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    isGM = author.server_permissions.administrator or author.server_permissions.manage_messages
    if author.id == char.userid or isGM:
        if char not in battle.participants or isGM:
            abl = char.abilities[codex[1].lower()]
            abl.setStep(codex[2:])
            return str(abl)
        else:
            return "You need Manage Messages or Administrator permission to modify characters during a battle!"
    else:
        return "You need Manage Messages or Administrator permission to modify other players' characters!"

def abilities(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    return char.listAbilities()

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
    isGM = author.server_permissions.administrator or author.server_permissions.manage_messages
    if author.id == char.userid or isGM:
        if char not in battle.participants or isGM:
            char.statPoints = makeStatsFromCodex(codex[1:])
            return str(char) + '\n\n{:d} stat points used.'.format(sum(char.statPoints.values()))
        else:
            return "You need Manage Messages or Administrator permission to restat your characters during a battle!"
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
/help ability: Deailed information on abilities and how to create them
/help ability2: The /editability command
/help ability3: An exaple ability
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
/abilities name: Show all of the abilities the named character has.
/invite: Show BattleBot's invite link.
/github: Show the link to this bot's sourcecode on GitHub.""",
        'battle': """Battle Commands
These commands are to be used during battle, and can only be used by the active player or a GM. See /help gm for more info.

/attack name: Punch the named character with a basic physical attack.
    This and the next few commands only work during your turn.
/move ...: Move along the specified path, as far as your speed roll allows.
    See /help move for info on the path syntax.
/ability abilityName [name ... | path]: Use an ability on the given targets, at the location at the end of the path, or on yourself if no targets or path are given.
    Path syntax is exactly the same as in /move.
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

Battlebot supports modifiers to stats, of the multiplicative and additive varieties.
When computing a character's effective stats, BattleBot first looks at their base stats and stat points, as described in /help stats.
Then, BattleBot goes through each multiplicative modifier for that stat, multiplies them together, and multiplies the number calculated above by that product.
After that, BattleBot adds together all the additive modifiers for the stat, and adds the sum to the above product.
Finally, after all that is done, BattleBot rounds the result down to an integer.

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
Unless they have no owner, which is also possible to do.""",
        'ability': """Abilities

BattleBot's ability system uses four commands.
/ability abilityName [targets | path]: Use an ability. An ability that is still on cooldown cannot be used
        until the cooldown expires; but otherwise, the restrictions on this are the same as for /attack.
    If it's a targeted ability, you can give it a list of targets. If none are given, targets yourself by default.
    If it's an AoE ability, give it a path to where you want the effect to be focused.
            The path syntax is exactly the same as that described in /help move.
/abilities name: List all of that character's abilities.
/makeability name abilityName range cooldown targetTypes [limit]: Create an ability, or change these fields
        of an ability that already exists.
    name: The name of the character that will have this ability.
    abilityName: The name of the ability.
    range: The maximum permissible distance between you and your target(s).
    cooldown: How many turns this ability will not be available after using it.
        Cooldown 1 means that you will not be able to use the ability again for one turn after using it
                (so you can use it every other turn).
        Cooldown 0 is no cooldown.
    targetTypes: Can take one of two forms.
        If "location" or "aoe", the ability will be an AoE ability aimed at a location in the grid.
        If not, then targetTypes must be "self", "ally", "enemy", or some combination thereof,
                such as "self ally" or "ally enemy".
            This restricts who the ability can target. Note that BattleBot does not have any way to know
            who is an ally and who is an enemy (yet), so "ally" and "enemy" are equivalent.
    limit: For AoE abilities, the radius of the affected area. For targeted abilities, the maximum number of targets.
            Deaults to 1.
/editability: See /help ability2""",
        'ability2': """The /editability Command

/editability name abilityName [n] action rpn ...: Edits the sequence of steps that the ability performs for each target.
    n: If given, replace line n rather than appending step n to the end of the list.
    rpn: The last parameter to /editability must be an RPN expression. It is executed whenever the ability is used,
            and its return value determines what will happen. See /rpn for details.
    action: What this step of the ability is supposed to do. Can take any one of the following formats:
        calc var: Executes the RPN expression, and stores its result in a variable called var for use in later steps.
            If the ability already has a step to calculate var, replace that step.
        var =: Same as calc var. Yes, that has to be a single equals sign.
        condition [cmp]: Compare the RPN result to 0 in one of six ways. If false, then stop execution
                of the ability right then and there and start over with the next target.
            Possible values of cmp are: <0, =0, ==0, >0, <=0, !0, !=0, >=0. If none are given, default to >0.
        effect [damage | apply] [self | target]: An effect of this ability.
            damage: Deal damage to a character. Does not roll dice, so use one of the roll commands in /help rpn2.
            apply: Apply a modifier to a character. The RPN expression must return a modifier: see /help rpn3.
                Defaults to apply if neither are given.
            self: The effect applies to the user of the ability, regardless of tho the target may be.
                    Usually superfluous, since you can target yourself.
            target: The effect applies to the target.
                Defaults to target if neither are given.
        flavor: Set the ability's flavor text.
        delete n: Delete step n from the ability.

Type /help ability3 for an example.""",
        'ability3': """A Shocking Example

Say you've got a character named "Zeus", and you want him to be able to summon lightning. You could type the following commands in this order:

/makeability zeus Smite 100 2 aoe 5
/editability zeus smite flavor Call down a bolt of lightning from the sky that will damage everyone within 5 tiles with up to 3x strengh, tapering off the farther they are away from the center of the strike.
/editability zeus smite dst = locus target pos dist
/editability zeus smite power = self atk 5 dst - * 3 * 5 //
/editability zeus smite effect damage power target def rolldmg

Now, you can use
/abilities Zeus
to have BattleBot return all of the above information to you.
If it's Zeus's turn to make a move,
/ability smite 6N
will use it on anyone and everyone within 11 tiles North of you.""",
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
/ : Division. May return a floating-point number: "5 2 /" evaluates to 2.5.
//: Floor division. Divides, then rounds down (i.e. toward -infinity). "5 2 //" evaluates to 2.

The rest of these have English names, and are not case-sensitive.
sum: Add together ALL the numbers on the stack, and push the result back on as the only element in the stack.
        So "1 2 3 4 5 sum" returns 15.

roll: Takes one argument off the stack. Roll that namy d10s, and push the sum back on the stack.
rollh: Like roll, except hide the individual rolls. Just return the sum.
rollu: As above, but hide the rolls if the user's stats are secret.
rollt: As above, but use the target's secret status.
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
    It's up to you to delete/edit your post to prevent players from reading the stats from it.
/excel: Generate an ODF spreadsheet of... something. I'm not sure what.""",
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
        elif codex[0] == 'ability':
            return useAbility(codex[1:], message.author)
        elif codex[0] == 'abilities':
            return abilities(codex[1:], message.author)
        elif codex[0] == 'makeability':
            return createAbility(codex[1:], message.author)
        elif codex[0] == 'editability':
            return editAbility(codex[1:], message.author)
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
        elif codex[0] == 'excel':
            data = createExcel(database[message.author.server.id].characters)
            return data
    return ""

@client.event
async def on_message(message):
    try:
        reply = getReply(message.content, message)
        if not isinstance(reply, str):
            if not reply['error']:
                await client.send_file(message.channel,reply['file'])
                if reply['deleteAfterUpload']:
                    os.remove(reply['file'])
            reply = reply["message"]
        if(len(reply) != 0):
            await client.send_message(message.channel, reply)
    except Exception as err:
        await client.send_message(message.channel, "`" + traceback.format_exc() + "`")

CURRENT_DB_VERSION = 14

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
                    if not hasattr(w, 'abilities'):
                        w.abilities = {}
                    if not hasattr(w, 'modifiers'):
                        w.clearModifiers()
                    if hasattr(w, 'orphanModifiers'):
                        delattr(w, 'orphanModifiers')
                    if not hasattr(w, 'ownedModifiers'):
                        w.ownedModifiers = []
                    if not hasattr(w, 'mention'):
                        w.mention = w.username
                        w.username = '_deprecated; please use /list to fix_'
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



