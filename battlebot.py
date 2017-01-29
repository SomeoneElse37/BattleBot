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
from classes.characters import Character,makeStatDict,defaultStats,statString
from classes.battles import Battle,clampPosWithinField
from classes.modifiers import Modifier
from classes.abilities import Ability
#other custom stuff that needs to get imported
from modules.help_pages import help_dict
from database.loadDatabase import makeDB
results = makeDB(argv)
token = results["token"]
db=results["db"]
results=None #we don't need it anymore. Though it isn't like we clear a lot of RAM with it, its better then nothing
generateExcel = True
if generateExcel:
    try:
        import modules.odsify_characters
        import os
    except ImportError:
        generateExcel=False
        print("Could not load odfpy. /excel is turned off")

def createExcel(characterList):
    if not generateExcel:
        return {'error':True,'message':"This command is not enabled right now"}
    else:
        pathToExcel = modules.odsify_characters.generateODSFromCharacters(characterList)
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
def createGuild(guild):
        if db.guildExists(guild):
            raise ValueError(guild.name + 'is already known to Battlebot!')
        else:
            db.makeBattle(guild.id,Battle(guild))
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
    db.insertChar(author.server,char)
    return str(char) + '\n\n{:d} stat points used.'.format(sum(char.statPoints.values()))

def clearBattle(codex, author):
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        db.clearBattle(author.server.id)
        return 'Battle data cleared.'
    else:
        return "You need Manage Messages or Administrator permission to clear the battle state!"

def joinBattle(codex, author):
    return db.addParticipant(codex[0],author.server.id)
    

def battleStatus(codex, author):
    battle = db.getBattle(author)
    return str(battle)

def charData(codex, author):
    char = db.getCharacter(author,codex)
    if char.userid == author.id:
        char.username = author.display_name
    return str(char)

def info(codex, author):
    if len(codex) == 0:
        return battleStatus(codex, author)
    else:
        return charData(codex, author)

def modifiers(codex, author):
    mods = db.getModifiers(author.server.id,codex[0].lower())
    #battle = database[author.server.id]
    #char = battle.characters[]
    #mods = char.listModifiers()
    if len(mods) > 0:
        return mods
    else:
        return char.name + ' has no modifiers.'

def deleteChar(codex, author):
    char = db.getCharacter(author.server.id,codex[0].lower())
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        db.deleteChar(author.server.id,codex[0])
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
        ##### This is where CHARACTER attributes get added! BATTLE attributes go above and an indent level to the left! Stop forgetting that, SE!








try:
    client.run(token)  # Blocking call; execution will not continue until client.run() returns
finally:
    db.exit()

#client.connect()
