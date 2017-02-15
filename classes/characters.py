import math
from random import randint, gauss, shuffle

from calc.dice import *
from calc.vector import *

def makeStatDict(hp, acc, eva, atk, dfn, spd):
        return dict(HP=hp, ACC=acc, EVA=eva, ATK=atk, DEF=dfn, SPD=spd)

def defaultStats(size):
        return makeStatDict(2**(size * 2), 2**(-size + 5), 2**(-size + 5), 2**(size * 4 - 2), 2**(size * 2), 2**(size))

def statString(stats):
    return "HP: {:d}  Accuracy: {:d}  Evasion: {:d}  Attack: {:d}  Defense: {:d}  Speed: {:d}".format(stats['HP'], stats['ACC'], stats['EVA'], stats['ATK'], stats['DEF'], stats['SPD'])

class Character:
    """Represents a character known to BattleBot."""

    sizeTiers = {
        'faerie': 1,
        'elf': 2,
        'human': 2,
        'werecat': 2,
        'elfcat': 2,
        'cyborg': 2,
        'robot': 2,
        'kraken': 3,
        'elfship': 3,
        'steamship': 3
        }

    baseStats = {
        'faerie': defaultStats(sizeTiers['faerie']),    # This sets the base stats for each species to the default, computed from their size.
        'elf': defaultStats(sizeTiers['elf']),          # If Lens wants different base stats for any/all races, I can hardcode that easily.
        'human': defaultStats(sizeTiers['human']),      # Allowing GMs to set that up per-server is doable, but would take a bit more work.
        'werecat': defaultStats(sizeTiers['werecat']),
        'elfcat': defaultStats(sizeTiers['elfcat']),
        'cyborg': defaultStats(sizeTiers['cyborg']),
        'robot': defaultStats(sizeTiers['robot']),
        'kraken': defaultStats(sizeTiers['kraken']),
        'elfship': defaultStats(sizeTiers['elfship']),
        'steamship': defaultStats(sizeTiers['steamship']),
        }

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
        if not race in Character.sizeTiers:
            raise ValueError("Invalid race.")
        self.mention = owner.mention
        self.username = owner.display_name
        self.userid = owner.id
        self.name = name
        self.race = race.lower()
        self.size = Character.sizeTiers[self.race]
        self.statPoints = statpoints
        self.baseStats = Character.baseStats[self.race]
        # Modifiers are stored in this dictionary.
        # The keys are the same as in all the various stat dictionaries. HP, ACC, EVA, etc.
        # Each value is a pair of lists. The first element in each pair is a list of multiplicative modifiers (e.g. 120% STR for 2 turns);
        # and the second element is a list of additive modifiers (e.g. +20 ACC until end of battle).
        # Each entry in these lists is itself a pair. The first element of this pair is the amount that the modifier changes the stat.
        # The second element is the duration of the modifier. This will be decremented at the end of each turn, and when it drops below zero, the modifier is removed.
        # Negative durations last forever.
        self.clearModifiers()
        self.ownedModifiers = []
        self.abilities = {}
        self.health = self.hp()
        self.pos = (0, 0)       # X and Y coordinates
        self.secret = secret    # If true, this character's stats will not be reported to players (used for some NPCs)
        self.ephemeral = false  # If true, this character will vanish on death, removing themself from the battle and revoking all their modifiers. Intended for minions.

    def isDead(self):
        return self.health <= 0

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

    def tickAbilities(self):
        for a in self.abilities.values():
            if a.timeout > 0:
                a.timeout -= 1

    def clearTimeouts(self):
        for a in self.abilities.values():
            a.timeout = 0

    def __str__(self):
        s1 = '...'
        s2 = '...'
        if not self.secret:
            s1 = statString(self.statPoints)
            s2 = statString(self.currentStats())
        return """Owner's username: {:s}
Owner's UUID: {:s}
Name: {:s}
Race: {:s}
Size Tier: {:d}
Stat Points: [{:s}]
Current Stats: [{:s}]
Abilities: {!s}
Location: ({:d}, {:d})
Health: {:d}""".format(self.username, self.userid, self.name, self.race, int(self.size), s1, s2, list(self.abilities.values()), int(self.pos[0]), int(self.pos[1]), int(self.health))

    # Reset health to the maximum, and clear all modifiers.
    def respawn(self):
        self.health = self.hp()
        self.clearModifiers()
        self.clearTimeouts()

    def onDeath(self):
        # Fancy on-death triggered abilities could go here.
        if self.ephemeral:
            self.respawn()

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
        self.health=int(self.health) #making sure its an int. Somehow, somewhere that got messed up while testing.
        self.health -= int(damage)
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
    def testMove(self, path, maxDist, stop, size, skipRoll=False):
        if skipRoll:
            out = ''
            dist = float('inf')
        else:
            out, dist = prettyRoll(self.spd(), secret=self.secret)
        if maxDist >= 0:        # Set the distance to travel to either the roll or the maxDist parameter, if given, whichever is less.
            dist = min(dist, maxDist)
            stop = False
        elif skipRoll:  # If we skipped the roll, then we'd better not try to go beyond the end of the path without some limit
            stop = True
        if stop:        # If the character is intended to stop at the end of the path, ensure that the last waypoint is "go nowhere"
            path.append((0, 0))
        pos = self.pos
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

    def listAbilities(self):
        out = ''
        for v in self.abilities.values():
            out += v.name + ':   '
            if self.secret:
                out += '...\n'
            else:
                out += str(v) + '\n\n'
        return out

    def distanceTo(self, pos):
        return distance(pos, self.pos)

    # Will be fancier once abilities are in
    def canMelee(self, pos):
        return self.distanceTo(pos) <= 1.5  # sqrt(2) ~= 1.414

    def inBox(self, minX, maxX, minY, maxY):
        return minX <= self.pos[0] <= maxX and minY <= self.pos[1] <= maxY

    def createAbility(self, codex):
        self.abilities[codex[0].lower()] = Ability(codex)

    def __eq__(self, other):
        return self.userid == other.userid and self.name == other.name

    def __repr__(self):
        return self.name



