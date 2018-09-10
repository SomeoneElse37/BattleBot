# discord.py
# Base code by Eruantien
# ANWA-apecific code by Someone Else 37 and lenscas

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
from classes.characters import *
from classes.battles import Battle
from classes.modifiers import Modifier
from classes.abilities import Ability

from calc.dice import *
from calc.vector import *
from calc.rpn import *
from calc.path import *

#other custom stuff that needs to get imported
from modules.help_pages import help_dict
from database.loadDatabase import makeDB

results = makeDB(argv)
token = results["token"]
db = results["db"]
results = None #we don't need it anymore. Though it isn't like we clear a lot of RAM with it, its better then nothing
generateExcel = True
allowRaceFallBackToHuman=True

if len(argv) >= 1 and argv[-1].lower() == 'fixminions':
    print('Marking all characters as non-minions.')
    db.deMinionFy()


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

##############################################
# Code for the various random calc functions #
##############################################

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

##################################################
##### Code for moderated battles begins here #####
##################################################

def makeStatsFromCodex(codex):
    if len(codex) >= 7:
        return makeStatDict(int(codex[0]), int(codex[1]), int(codex[2]), int(codex[3]), int(codex[4]), int(codex[5]), int(codex[6]))
    else:
        return makeStatDict(0, 0, 0, 0, 0, 0, 0)

def stats(codex):
    out = '`{:11s}  {:>5s} {:>5s} {:>5s} {:>5s} {:>5s} {:>5s} {:>5s}`\n'.format('Size Tier', 'HP', 'Acc', 'Eva', 'Atk', 'Def', 'Spd', 'Ran')
    sp = statFreePoints(1);
    sv = statValues(1);
    out += '`1 (Faerie)`\n'
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`\n'.format('Free Points', sp['HP'], sp['ACC'], sp['EVA'], sp['ATK'], sp['DEF'], sp['SPD'], sp['RAN'])
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`\n'.format('Point Value', sv['HP'], sv['ACC'], sv['EVA'], sv['ATK'], sv['DEF'], sv['SPD'], sv['RAN'])
    sp = statFreePoints(2);
    sv = statValues(2);
    out += '`2 (Werecat)`\n'
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`\n'.format('Free Points', sp['HP'], sp['ACC'], sp['EVA'], sp['ATK'], sp['DEF'], sp['SPD'], sp['RAN'])
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`\n'.format('Point Value', sv['HP'], sv['ACC'], sv['EVA'], sv['ATK'], sv['DEF'], sv['SPD'], sv['RAN'])
    sp = statFreePoints(3);
    sv = statValues(3);
    out += '`3 (Kraken)`\n'
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`\n'.format('Free Points', sp['HP'], sp['ACC'], sp['EVA'], sp['ATK'], sp['DEF'], sp['SPD'], sp['RAN'])
    out += '`{:11s}: {:5d} {:5d} {:5d} {:5d} {:5d} {:5d} {:5d}`'.format(  'Point Value', sv['HP'], sv['ACC'], sv['EVA'], sv['ATK'], sv['DEF'], sv['SPD'], sv['RAN'])
    return out

def makeChar(codex, author):
    extraText=""
    char = Character(author, codex[0], codex[1].lower(), makeStatsFromCodex(codex[2:]))
    if char.usedFallBack:
        if not allowRaceFallBackToHuman:
            raise ValueError("not a valid race")
        extraText = "Race "+codex[1]+ " did not exist, falling back to human \n"
    db.insertCharacter(author.server,char)
    return extraText+(str(char) + '\n\n{:d} stat points used.'.format(sum(char.statPoints.values())))

def clearBattle(codex, author):
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        db.clearBattle(author.server.id)
        return 'Battle data cleared.'
    else:
        return "You need Manage Messages or Administrator permission to clear the battle state!"

def joinBattle(codex, author):
    return db.addParticipant(codex[0], author.server.id)

def battleStatus(codex, author):
    battle = db.getBattle(author.server.id)
    return str(battle)

def charData(codex, author):
    char = db.getCharacter(author.server.id, codex[0])
    if char.userid == author.id:
        char.username = author.display_name
        char.mention = author.mention
    return str(char)

def info(codex, author):
    if len(codex) == 0:
        return battleStatus(codex, author)
    else:
        return charData(codex, author)

def modifiers(codex, author):
    mods = db.getModifiers(author.server.id, codex[0].lower())
    #battle = database[author.server.id]
    #char = battle.characters[]
    #mods = char.listModifiers()
    if len(mods) > 0:
        return mods
    else:
        return char.name + ' has no modifiers.'

def deleteChar(codex, author):
    char = db.getCharacter(author.server.id, codex[0].lower())
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        db.deleteChar(author.server.id,codex[0])
        return codex[0] + ' was successfully deleted.'
    else:
        return "You need Manage Messages or Administrator permission to delete other players' characters!"

def passTurn(codex, author):
    char = db.getCurrentChar(author.server.id)
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return 'Turn passed successfully.\n\n' + db.doPassTurn(author.server.id)
    else:
        return "You need Manage Messages or Administrator permission to take control of other players' characters!"

def basicAttack(codex, author):
    char = db.getCurrentChar(author.server.id)
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return db.doBasicAttack(codex[0],author.server.id) #battle.basicAttack(codex[0]) + '\n\n' + battle.currentCharPretty()
    else:
        return "You need Manage Messages or Administrator permission to take control of other players' characters!"

def move(codex, author):
    char = db.getCurrentChar(author.server.id)#battle.currentChar()
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return db.doMove(codex,author.server.id)#battle.move(codex) + '\n\n' + battle.currentCharPretty()
    else:
        return "You need Manage Messages or Administrator permission to take control of other players' characters!"

# Use an ability.
def useAbility(codex, author):
    #battle = database[author.server.id]
    char = db.getCurrentChar(author.server.id)
    if author.id == char.userid or author.server_permissions.administrator or author.server_permissions.manage_messages:
        return db.doAbility(codex,author.server.id)#battle.useAbility(codex) + '\n\n' + battle.currentCharPretty()
    else:
        return "You need Manage Messages or Administrator permission to take control of other players' characters!"

def createAbility(codex, author):
    char = db.getCharacter(author.server.id, codex[0].lower())
    #battle = database[author.server.id]
    #char = battle.characters[codex[0].lower()]
    isGM = author.server_permissions.administrator or author.server_permissions.manage_messages
    if author.id == char.userid or isGM:
        result = db.insertAbility(author.server.id, codex, isGM)
        if result:
            return result
        return "You need Manage Messages or Administrator permission to modify characters during a battle!"
#        if char not in battle.participants or isGM:
#            try:
#                abl = char.abilities[codex[1].lower()]
#                abl.setFields(codex[2:])
#                return str(abl)
#            except KeyError:
#                abl = Ability(codex[1:])
#                char.abilities[abl.name.lower()] = abl
#                return str(abl)
#        else:
#            return "You need Manage Messages or Administrator permission to modify characters during a battle!"
    else:
        return "You need Manage Messages or Administrator permission to modify other players' characters!"

def editAbility(codex, author):
    #battle = database[author.server.id]
    #char = battle.characters[codex[0].lower()]
    char = db.getCharacter(author.server.id, codex[0].lower())
    isGM = author.server_permissions.administrator or author.server_permissions.manage_messages
    if author.id == char.userid or isGM:
        result = db.updateAbility(author.server.id, codex, isGM)
        if result:
            return result
        return "You need Manage Messages or Administrator permission to modify characters during a battle!"
#        if char not in battle.participants or isGM:
#            abl = char.abilities[codex[1].lower()]
#            abl.setStep(codex[2:])
#            return str(abl)
#        else:
#            return "You need Manage Messages or Administrator permission to modify characters during a battle!"
    else:
        return "You need Manage Messages or Administrator permission to modify other players' characters!"

def abilities(codex, author):
    #battle = database[author.server.id]
    #char = battle.characters[codex[0].lower()]
    return db.getAbilities(author.server.id,codex[0].lower())# char.listAbilities()

# /map
# /map scale
# /map centerX centerY
# /map centerX canterY radius
# /map x1 x2 y1 y2
# /map x1 x2 y1 y2 scale
def showMap(codex, author):
    battle = db.getBattle(author.server.id)#database[author.server.id]
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
    char = db.getCharacter(author.server.id, codex[0].lower())
    #battle = database[author.server.id]
    #char = battle.characters[codex[0].lower()]
    isGM = author.server_permissions.administrator or author.server_permissions.manage_messages
    if author.id == char.userid or isGM:
        result = db.updateStats(author.server.id, codex[0].lower(), makeStatsFromCodex(codex[1:]), isGM)
        if result:
            return result
        return "You need Manage Messages or Administrator permission to restat your characters during a battle!"
#        if char not in battle.participants or isGM:
#            char.statPoints = makeStatsFromCodex(codex[1:])
#            return str(char) + '\n\n{:d} stat points used.'.format(sum(char.statPoints.values()))
#        else:
#            return "You need Manage Messages or Administrator permission to restat your characters during a battle!"
    else:
        return "You need Manage Messages or Administrator permission to restat other players' characters!"

def setAttackRange(codex, author):
    char = db.getCharacter(author.server.id, codex[0].lower())
    isGM = author.server_permissions.administrator or author.server_permissions.manage_messages
    if author.id == char.userid or isGM:
        result = db.setAttackRange(author.server.id, codex[0].lower(), codex[1], isGM)
        if result is not None:
            return result
        return "You need Manage Messages or Administrator permission to modify your characters during a battle!"
    else:
        return "You need Manage Messages or Administrator permission to modify other players' characters!"

# Will be set to discord.Client() later on; sendToServer needs to know of this right now (but will not be called until later)
client = None;

# Creates a copy of the named Character and sends it to an entirely different server, specified either by ID or by name
def sendToServer(codex, author):
    targetBattle = None
    battleName = ' '.join(codex[1:])
    matchedID = False
    try:
        targetBattle = db.getBattle(codex[1])   # May need to be int(codex[1])
        matchedID = True
    except KeyError:
        for guild in client.servers:
            if guild.name == battleName:
                try:
                    targetBattle = db.getBattle(guild.id)
                except KeyError:
                    db.createGuild(guild)
                    targetBattle = db.getBattle(guild.id)
                break
            elif guild.id == codex[1]:      # May also need to be int(codex[1])
                db.createGuild(guild)       # If we're here, the user named a guild ID known to BattleBot that does not already have
                targetBattle = db.getBattle(guild.id)   # an associated Battle object. So create one.
                matchedID = True
                break
    if targetBattle is None:
        log = "Server '{!s}' not found. Known servers:\n".format(codex[1])
        for guild in client.servers:
            log += '\n{} ({})'.format(guild.name, guild.id)
        return log
    char = db.getCharacter(author.server.id, codex[0].lower())
    new = char.copy()
    new.mention = author.mention
    new.username = author.display_name
    new.userid = author.id
    hasNewName = False
    if matchedID and len(codex) >= 3:
        new.name = codex[2]
        hasNewName = True
    try:
        targetBattle.addCharacter(new)
    except ValueError as e:
        if e.args[0].startswith('There is already '):
            return '''There is already a character on '{2}' named {1}.

Try deleting {1} from '{2}' first, or typing /send {0} {3} {4}'''.format(char.name, new.name, targetBattle.name, targetBattle.id, 'someOtherName' if hasNewName else 'aNewName')
        else:
            raise
    return "{} successfully copied to '{}'.".format(new.name, targetBattle.name)

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

#This needs to be better abstracted if we want to switch to SQL.
def addModifier(codex, author):
    battle = db.getBattle(author.server.id)     #database[author.server.id]
    char = db.getCharacter(author.server.id, codex[0].lower())   #battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        owner = db.getCharacter(author.server.id,codex[-1].lower())  #battle.characters[codex[-1].lower()]
        mod = Modifier(parseModifier(codex[1:]), holder=char, owner=owner) # Will automatically attach itself to the correct characters
        return char.listModifiers()
    else:
        return "You need Manage Messages or Administrator permission to create modifiers!"

def warp(codex, author):
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        return db.updateLocation(author.server.id, codex[0].lower(), int(codex[1]), int(codex[2]))
        #return str(char)
    else:
        return "You need Manage Messages or Administrator permission to teleport characters!"

def setHealth(codex, author):
    #battle = database[author.server.id]
    #char = battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        if len(codex) > 1:
            char = db.updateHealth(author.server.id,codex[0].lower(),codex[1])
            #char.health = int(codex[1])
        else:
            char = db.respawnChar(author.server.id,codex[0].lower())
            #char.respawn()
        return str(char)
    else:
        return "You need Manage Messages or Administrator permission to set characters' HP!"

def toggleSecret(codex, author):
    #battle = database[author.server.id]
    #char = battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        char= db.toggleSecretChar(author.server.id, codex[0].lower())
        #char.secret = not char.secret
        return str(char)
    else:
        return "You need Manage Messages or Administrator permission to change characters' visibility!"

def gm_attack(codex, author):
    #battle = database[author.server.id]
    #char = battle.characters[codex[0].lower()]
    char =  db.getCharacter(author.server.id, codex[0].lower())
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

def gm_ability(codex, author):
    battle = db.getBattle(author.server.id)
    char = db.getCharacter(author.server.id, codex[0].lower())
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        ablName = codex[1]
        codex = codex[2:]
        if codex[0] == 'as':
            user = db.getCharacter(author.server.id, codex[1].lower())
            codex = codex[2:]
        else:
            user = None
        return battle.useAbilityOf(char, ablName, codex, user=user, ignoreTimeout=True)
    else:
        return "You need Manage Messages or Administrator permission to perform GM ability-activations!"

def addMark(codex,author):
    if len(codex)==1:
        codex.append(0)
    currentRound = db.getCurrentRound(author.server.id)
    codex[1] = currentRound + int(codex[1])
    db.addMark(author.server.id,codex[0],int(codex[1]))
    return "Mark " + str(codex[0]) + " is set for round " + str(codex[1]) +" and it is currently round " + str(currentRound)

def showMarks(codex,author):
    marks     = db.getMarks(author.server.id)
    currRound = db.getCurrentRound(author.server.id)
    text = "It is currently round "+str(currRound)
    if len(marks)==0:
        return text + "\n there are currently no marks"
    for key in range(len(marks)):
        mark = marks[key]
        text= text+"\n "+str(key)+" **"+marks[key]['name']+"**"
        if mark['turn']< currRound:
            happenedAt = str(currRound-mark['turn'])
            text = text +" has happened **"+happenedAt +"** rounds from now"
        elif mark['turn']>currRound:
            willHappen = str(mark['turn']-currRound)
            text=text+" will happen **"+willHappen +"** rounds from now"
        else:
            text=text+" will happen right now!"
    return text

def removeMark(codex,author):
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        db.removeMark(author.server.id,codex[0])
        return showMarks(codex,author)
    else:
        return "You need Manage Messages or Administrator permission to remove marks!"

def setSize(codex, author):
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        return db.updateSize(author.server.id, int(codex[0]), int(codex[1]))
    else:
        return "You need Manage Messages or Administrator permission to change the size of the battlefield!"

def toggleTurnSkip(codex, author):
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        return "Turn skip set to {!s}.".format(db.toggleTurnSkip(author.server.id, codex[0]))
    else:
        return "You need Manage Messages or Administrator permission to force characters to skip their turns!"

def makeMinion(codex, author):
    # print(len(codex))
    return str(db.minionByChar(codex[0], author.server.id))

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
                return testRPN(codex[1:], data=db.getBattle(message.author.server.id).characters)
        elif codex[0] == 'help':
            if len(codex) > 1:
                key = codex[1].lower()
                if key in help_dict:
                    entry = help_dict[key]
                    try:
                        if len(codex) > 2:
                            key2 = codex[2].lower()
                            if key2 in entry:
                                return entry.get(key2)  # Using .get() instead of the usual dict[key] syntax because [key] might work on a string,
                        return entry.get(key)           # and if entry is a string, I want to be sure that this throws an exception
                    except (TypeError, NameError, AttributeError):
                        return entry
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
        elif codex[0] == 'setreach':
            return setAttackRange(codex[1:], message.author)
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
        elif codex[0] == 'send':
            return sendToServer(codex[1:], message.author)
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
        elif codex[0] == 'gmability':
            return gm_ability(codex[1:], message.author)
        elif codex[0] == 'setsize':
            return setSize(codex[1:], message.author)
        elif codex[0] == 'github':
            return git_link
        elif codex[0] == 'invite':
            return get_invite(client.user.id)
        elif codex[0] == 'excel':
            data = createExcel(db.getAllCharacters(message.author.server.id))
            return data
        elif codex[0] == "makeMinion":
            return makeMinion(codex[1:], message.author)
        elif codex[0] == "toggleTurnSkip":
            return toggleTurnSkip(codex[1:], message.author)
        elif codex[0] == "addMark":
            return addMark(codex[1:], message.author)
        elif codex[0] == "showMarks":
            return showMarks(codex[1:],message.author)
        elif codex[0] == "removeMark":
            return removeMark(codex[1:],message.author)
    return ""

@client.event
async def on_message(message):
    try:
        reply = getReply(message.content, message)
        if not isinstance(reply, str):
            if not reply['error']:
                await client.send_file(message.channel,reply['file']) # This is invalidated in the new discord.py; use message.channel.send()
                if reply['deleteAfterUpload']:
                    os.remove(reply['file'])
            reply = reply["message"]
        if(len(reply) != 0):
            await message.channel.send(reply)
    except Exception as err:
        await message.channel.send("`" + traceback.format_exc() + "`")

try:
    client.run(token)  # Blocking call; execution will not continue until client.run() returns
finally:
    db.exitDB()
    logging.shutdown()

#client.connect()
