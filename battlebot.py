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

# function roll(n) {
#     if(n <= 10) {
#         <insert the roll-and-add loop here>
#     } else {
#         return gauss() * sqrt(n) * sqrt(8.25) + n * 5.5;
#     }
# }
#
# function gauss() {
#     float U = randUniform(0, 1);
#     float V = randUniform(0, 1);
#     return sqrt(-2 * ln(U)) * cos(2 * pi * V);
# }

# ((1/n sum(X1..Xn)) - mu) * sqrt(n) = N(0, variance(X))
# (1/n sum(X1..Xn)) - mu = N(0, variance(X)) / sqrt(n)
# 1/n sum(X1..Xn) = N(0, variance(X)) / sqrt(n) + mean(X)
# sum(X1..Xn) = n * (N(0, variance(X)) / sqrt(n) + mean(X))
# sum(X1..Xn) = (N(0, 1) * stdev(X) / sqrt(n) + mean(X)) * n

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

def checkString(r1, r2):
    diff = r1 - r2
    if diff < -20:
        return "The attack missed by a mile."
    elif diff <= 0:
        return "Failure. The attack missed."
    elif diff <= 20:
        return "Success! The attack connects."
    else:
        return "Critical hit? Maybe?"

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
def prettyCheck(acc, eva, secrets=(False, False)):
    s1, r1 = prettyRoll(acc, secrets[0])
    s2, r2 = prettyRoll(eva, secrets[1])
    return s1 + '\n' + s2 + '\n' + checkString(r1, r2), r1 > r2

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

BASE_RANGE = 16     # The miminum distance, in range units, considered to be in Sword Range
HIGHEST_RANGE_KEY = len(rangeNames) - 1
BOXING_MAX = BASE_RANGE - 1     # Used when checking that basic physical attacks can actually be done

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

def retreat(codex):
    return(formatRetreat(int(codex[0]), d10(int(codex[1]), 10)))

def approachCenter(r, spd):
    dx = sum(spd)
    return formatRoll(spd) + '\n' + str(dx) + ': Moved from ' + str(r) + ' (' + rangestring(r) + ') to ' + str(max(0, r - dx)) + ' (' + rangestring(r - dx) + ').'

def approachChar(r1, spd, r2):
    dx = sum(spd)
    rangediff = abs(r1 - r2)

            # For 1..dx, subtract 1 from r1 or r2, whichever is bigger.

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
        r1final = r1final - int((dx - rangediff) / 2) - (dx - rangediff) % 2
        r2final = r2final - int((dx - rangediff) / 2)
    else:
        if r1 > r2:
            r1final = r1 - dx
        else:
            r2final = r2 - dx

    out = formatRoll(spd) + '\n'
    out = out + str(dx) + ': Pursuer moved from ' + str(r1) + ' (' + rangestring(r1) + ') to ' + str(max(0, r1final)) + ' (' + rangestring(r1final) + ').\n'
    out = out + 'Target moved from ' + str(r2) + ' (' + rangestring(r2) + ') to ' + str(max(0, r2final)) + ' (' + rangestring(r2final) + ').'
    return out

def approach(codex):
    if len(codex) <= 2:
        return(approachCenter(int(codex[0]), d10(int(codex[1]), 10)))
    else:
        return(approachChar(int(codex[0]), d10(int(codex[1]), 10), int(codex[2])))


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
    return makeStatDict(int(codex[0]), int(codex[1]), int(codex[2]), int(codex[3]), int(codex[4]), int(codex[5]))

def defaultStats(size):
    return makeStatDict(2**(size * 2), 2**(-size + 5), 2**(-size + 5), 2**(size * 4 - 2), 2**(size * 2), 2**(size))

baseStats = {
        'faerie': defaultStats(sizeTiers['faerie']),    # Does this even work? At any rate, it'll let me
        'elf': defaultStats(sizeTiers['elf']),          # tweak the base stats for each race individually
        'werecat': defaultStats(sizeTiers['werecat']),  # if/when Lens decides to.
        'elfcat': defaultStats(sizeTiers['elfcat']),
        'cyborg': defaultStats(sizeTiers['cyborg']),
        'robot': defaultStats(sizeTiers['robot']),
        'kraken': defaultStats(sizeTiers['kraken']),
        'elfship': defaultStats(sizeTiers['elfship']),
        'steamship': defaultStats(sizeTiers['steamship']),
        }

def statstring(stats):
    return "HP: {:d}  Accuracy: {:d}  Evasion: {:d}  Attack: {:d}  Defense: {:d}  Speed: {:d}".format(stats['HP'],
            stats['ACC'], stats['EVA'], stats['ATK'], stats['DEF'], stats['SPD'])

class Character:
    """Represents a character known to BattleBot."""

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
        self.abilities = []     # Ability system is planned, but NYI
        self.modifiers = []     # Modifier system is also planned, but NYI
        self.health = self.hp()
        self.location = 0
        self.secret = secret    # If true, this character's stats will not be reported to players (used for some NPCs)

    # Returns the characters hp STAT, i.e. their MAXIMUM health, NOT their current health. Use the self.health attribute for that.
    def hp(self):
        return int(self.baseStats['HP'] * (1 + self.statPoints['HP'] / 8))  # Modifiers will, well, modify this

    # Return the character's current Accuracy, accounting for all modifiers (once they're implemented)
    def acc(self):
        return int(self.baseStats['ACC'] * (1 + self.statPoints['ACC'] / 8))

    def eva(self):
        return int(self.baseStats['EVA'] * (1 + self.statPoints['EVA'] / 8))

    def atk(self):
        return int(self.baseStats['ATK'] * (1 + self.statPoints['ATK'] / 8))

    def dfn(self):
        return int(self.baseStats['DEF'] * (1 + self.statPoints['DEF'] / 8))

    def spd(self):
        return int(self.baseStats['SPD'] * (1 + self.statPoints['SPD'] / 8))

    def currentStats(self):
        return makeStatDict(self.hp(), self.acc(), self.eva(), self.atk(), self.dfn(), self.spd())

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
Location: {:d}
Health: {:d}""".format(self.username, self.userid, self.name, self.race, self.size, s1, s2, self.location, self.health)

    def respawn(self):
        self.health = self.hp()

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
        self.radius = -1        # Radius of the battlefield; the maximum distance anyone will be able to be from the center; -1 is no limit

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
            if char.location > self.radius:     # A little sanity check here.
                char.location = self.radius

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
            out += '\n\nSorted by Location (current range):\n'
            for char in sorted(self.participants, key=lambda char: char.location):
                out += char.name + '(' + str(char.location) + ') '
            out += '\n\n' + self.currentCharPretty()
            if self.turn == -1:
                out += "\n\nThe battle has yet to begin!"
        else:
            out += '\n\nThere is no active battle.'
        return out

    def delete(self, name):
        char = self.characters[name.lower()]
        del self.characters[name.lower()]
        try:
            self.removeParticipantByChar(char)
        except ValueError:
            pass

    def passTurn(self):
        if self.turn == -1:
            self.turn = 1
        else:
            self.turn += 1
        if self.turn >= len(self.participants):
            self.turn = 0

    def basicAttack(self, targetName):
        user = self.currentChar()
        target = self.characters[targetName.lower()]
        if target not in self.participants:
            return target.name + ' is not participating in the battle!'
        if user.location > BOXING_MAX:
            return 'You can only use basic physical attacks at boxing range!'
        if target.location > BOXING_MAX:
            return target.name + ' is at ' + rangestring(target.location) + '!'
        out, damage = target.rollFullAttack(user.acc(), user.atk(), secret=user.secret)
        if target.health <= 0:
            self.removeParticipantByChar(target)
            target.respawn()
        self.passTurn()
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
    return str(char)

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

def warp(codex, author):
    battle = database[author.server.id]
    char = battle.characters[codex[0].lower()]
    if author.server_permissions.administrator or author.server_permissions.manage_messages:
        char.location = int(codex[1])
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

help_calc = """Calculation Commands:
/calc roll XdY: Roll X dYs and add the results
/calc check acc eva: Roll a BtNS-style accuracy check
/calc damage atk def: Do a damage roll in my fancy BtNS-inspired way
/calc avgdmg atk def: Do 1000 damage rolls, calculate a bunch of summary statistics, and produce a histogram.
   Each `#` in the histogram represents 10 rolls that dealt that amount of damage, `|` is 5, `:` is 2, and `.` is 1
/calc attack acc atk eva def hp: Roll accuracy and damage repeatedly, until HP damage has been dealt.
/calc repattack acc atk eva def hp: Run /attack many times over, then return summary statistics and a histogram.
/calc range r: Convert a range integer into a human-readable string
/calc rangedump: Generate a list of all the range ranges, and their names
/calc rangelookup strn: Look up the given range string, and return the range integers that it corresponds to.
    Only requires that the given name be a substring of the name in BattleBot's sourcecode, and ignores case:
    /calc rangelookup ortBOW works fine.
/calc approach r spd [r2]: Do an approach roll, approaching the melee circle or, optionally, another character at range r2
/calc retreat r spd: Do a retreat roll
/calc defaultstats: Print out the default stats for all the size tiers
/calc testStatRoll n bucketSize: Test my new statical dice-rolling code against the count-and-add code by rolling n d10s.
    Returns a histogram. Each row is a bucket of bucketSize, collecting all rolls from one algorithm within its range.
    The even-numbered rows correspond to the count-and-add algorithm; the odd ones to the new statistical algorithm.
/calc help: show this message again"""

help_gm = """GM commands:
    The following behavior only functions if you are a GM, meaning that you have
    either Administrator or Manage Messages permission on the server.
/pass, /attack, /delete: GMs can use these commands to control/delete other players' characters.
/warp name dist: Teleports the named character to the given location distance.
/sethp name [health]: Sets the named character's current health, or to their maximum health is none is specified.
/togglesecret name: Toggle whether the named character's stats are hidden from players.
/gmattack name acc atk [secret?]: Perform at attack with the given Accuracy and Attack against the named character.
    If 0 or a negative number is specified for acc or atk, those stats will not be rolled.
    If anything at all is given for the fourth parameter, the bot will not echo the Accuracy or Attack specified.
    It's up to you to delete/edit your post to prevent players from reading the stats from it.
/help gm: show this message again"""


help_msg = """Battlebot Commands:
/invite: Show this bot's invite link
/roll XdY: Roll X dYs and add the results
/defaultstats: Print out the default stats for all the size tiers
/makechar name race hp acc eva atk dfn spd: Create a character with the given name, race, and stat point distribution
    Accepted races: faerie, elf, werecat, elfcat, cyborg, robot, kraken, elfship, steamship
/join name: Join the battle ongoing on your server.
    Support for using /join with no argument to automatically add one of your characters is planned, but NYI.
/attack name: Punch the named character with a basic physical attack. Only works if it's currently your turn.
/pass: Pass your turn. Only works if it is currently your turn.
/list: List a bunch of info about the current state of the battle- who's participating, turn order, etc.
/list name: Show all the info about the named character.
/clear: Clear the current battle and heal and respawn all participants. Only GMs can do this.
/delete name: Delete a character. Only works on characters you created. Warning, this is permanent!
/help calc: Show help for all the old calculation commands
/help gm: Show help for the various GM commands.
/help: Show this message again"""

PREFIX = '/'

def getReply(content, message):
    if content.startswith(PREFIX):
        codex = content[len(PREFIX):].split(' ');
        if codex[0] == 'calc':
            codex = codex[1:]
            if codex[0] == 'help':
                return help_calc
            elif codex[0] == 'roll':
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
                return approach(codex[1:])
            elif codex[0] == 'retreat':
                return retreat(codex[1:])
            elif codex[0] == 'defaultstats':
                return stats(codex[1:])
            elif codex[0] == 'testStatRoll':
                return testStatisticRolls(codex[1:])
        elif codex[0] == 'help':
            if len(codex) > 1:
                if codex[1] == 'calc':
                    return help_calc
                elif codex[1] == 'gm':
                    return help_gm
            return help_msg
        elif codex[0] == 'roll':
            return roll(codex[1:])
        elif codex[0] == 'defaultstats':
            return stats(codex[1:])
        elif codex[0] == 'makechar':
            return makeChar(codex[1:], message.author)
        elif codex[0] == 'join':
            return joinBattle(codex[1:], message.author)
        elif codex[0] == 'list':
            return info(codex[1:], message.author)
        elif codex[0] == 'attack':
            return basicAttack(codex[1:], message.author)
        elif codex[0] == 'pass':
            return passTurn(codex[1:], message.author)
        elif codex[0] == 'clear':
            return clearBattle(codex[1:], message.author)
        elif codex[0] == 'delete':
            return deleteChar(codex[1:], message.author)
        elif codex[0] == 'warp':
            return warp(codex[1:], message.author)
        elif codex[0] == 'sethp':
            return setHealth(codex[1:], message.author)
        elif codex[0] == 'togglesecret':
            return toggleSecret(codex[1:], message.author)
        elif codex[0] == 'gmattack':
            return gm_attack(codex[1:], message.author)
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

CURRENT_DB_VERSION = 2

def updateDBFormat():
    if 'version' not in database or database['version'] < CURRENT_DB_VERSION:
        print("Updating database format.")
        database['version'] = CURRENT_DB_VERSION
        for k, v in database.items():
            if k != 'version':
                # Battle attributes: characters, participants, turn, id, name, radius
                if not hasattr(v, 'radius'):
                    v.radius = -1
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

token = ''

datafile = 'battlebot.pickle'
dev_datafile = 'battlebot_dev.pickle'

if len(argv) > 1 and argv[1] == 'dev':
    print('Battlebot running in dev mode.')
    with open('devbot.token', mode='r') as f:
        token = f.readline()
    datafile = dev_datafile
else:
    print('Battlebot running in release mode.')
    with open('bot.token', mode='r') as f:
        token = f.readline()

try:
    with open(datafile, 'rb') as f:
        database = pickle.load(f)
    updateDBFormat()
    print(str(len(database) - 1) + ' guilds loaded.')
except FileNotFoundError:
    print('Database could not be loaded. Creating an empty database.')


client.run(token)  # Blocking call; execution will not continue until client.run() returns

with open(datafile, 'wb') as f:
    pickle.dump(database, f, pickle.HIGHEST_PROTOCOL)

print('Database saved to disk.')

#client.connect()



