from random import choice

from calc.dice import *
from calc.vector import *
from calc.path import *

from util.errors import *

# Awful O(n^2) stupidity, I know, but this needs to work on things that aren't hashable.
def _removeDups(xs):
    out = []
    for x in xs:
        isNew = True
        for y in out:
            if y is x:
                isTrue = False
                break
        if isNew:
            out.append(x)
    return out

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
        self.moved = False      # True if the current character has /moved during their turn
        self.attacked = False   # True if the current character has /attacked or used an /ability during their turn
        self.marks=[] #this stores various marks in the battle. Can be used as reminders for when stuff will happens or has happened
        self.atRound=0 #At which round we are currently. Used by the mark system

    def addCharacter(self, char):
        if char.name.lower() not in self.characters:
            self.characters[char.name.lower()] = char
        else:
            raise ValueError("There is already a character named " + char.name + "!")

    def clear(self):
        remove=[]
        for k, v in self.characters.items():
            v.respawn()
            v.minionCount = 0
            if v.isMinion:
                remove.append(k)
        for k in remove: del self.characters[k]
        self.participants = []
        self.turn = -1
        self.atRound=1
        self.marks=[]

    # Warning: May give undefined behavior if char is not already in the characters dictionary
    def addParticipantByChar(self, char):
        if char in self.participants:
            raise ValueError(char.name + " is already participating!")
        else:
            char.respawn()
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
        print(str(self.characters.keys()))
        self.addParticipantByChar(self.characters[name.lower()])

    # Clones the named character as a minion, then adds the minion to the current battle.
    def makeMinion(self, name):
        char = self.characters[name.lower()]
        minion = char.minionFy()
        self.addCharacter(minion)
        self.addParticipantByChar(minion)
        return minion

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
        char = self.currentChar()
        return 'It is ' + char.name + "'s turn. " + char.mention

    def __str__(self):
        out = self.name + ' (' + self.id + ')\n'
        out += 'Characters:\n'
        for k, v in self.characters.items():
            out += v.name + ' '
        out += '\nSize: {!s}'.format(self.size)
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

    def __repr__(self):
        return '{} ({})'.format(self.name, self.id)

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

    def passTurn(self):
        while True:
            self.currentChar().tickModifiers()
            self.currentChar().tickAbilities()
            self.moved = False
            self.attacked = False
            if self.turn == -1:
                self.turn = 1
            else:
                self.turn += 1
            if self.turn >= len(self.participants):
                self.turn = 0
                self.atRound +=1
            # print(self.turn)
            # print(self.currentChar())
            try:
                currentChar = self.currentChar()
                if currentChar.isDead():
                    continue
                for abl in currentChar.getAutoAbilities():
                    abl.execute(currentChar, self.participants, targets=[currentChar], locus=currentChar.pos)
                if currentChar.forceTurnSkip:
                    continue
                break
            except AttributeError:
                break

    def availableActions(self):
        if self.moved and self.attacked:
            return ''
        elif self.attacked:
            return '\n\nYou may use /move to move, or /pass to pass your turn.'
        elif self.moved:
            return '\n\nYou may use /attack to perform a basic physical attack, /ability to use an ability, or /pass to pass your turn.'
        else:
            return '\n\nYou may use /move and either /attack or /ability this turn, if you wish.'

    def onDeath(self, char):
        char.onDeath()
        if char.ephemeral:
            removeParticipantByChar(char)

    def basicAttack(self, targetName):
        if self.attacked:
            return self.availableActions()
        user = self.currentChar()
        target = self.characters[targetName.lower()]
        if target not in self.participants:
            return target.name + ' is not participating in the battle!'
        if not user.canMelee(target.pos):
            return target.name + ' is too far away!'
        if target.isDead():
            return target.name + ' is dead!'
        out, damage = target.rollFullAttack(user.acc(), user.atk(), secret=user.secret)
        if target.health <= 0:
            self.onDeath(target)
            #self.removeParticipantByChar(target)
            #target.respawn()
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
                        raise AbilityError('Expected an integer after - sign; got ' + codex[0])
                else:
                    raise AbilityError('Could not parse direction or waypoint: ' + codex[0]) # If none of the above matched, raise an exception
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

    def useAbilityOf(self, char, abilityName, codex, user=None, ignoreTimeout=False):
        if user is None:
            user = char
        ability = char.abilities[abilityName.lower()]
        prevTimeout = ability.timeout
        if ignoreTimeout:
            ability.timeout = 0
        out = ''
        prevDeadChars = [ch for ch in self.participants if ch.isDead()]
        if 'reaction' in ability.targets:
            raise AbilityError("This is a reaction. You can't just activate it anytime.")
        if 'auto' in ability.targets:
            raise AbilityError("This is an automatic ability. It'll activate automatically at the end of your turn.")
        elif 'random' in ability.targets:
            out += ability.execute(user, self.participants)
        elif 'location' in ability.targets:
            path, maxDist, stop = self.parseDirectionList(user.pos, codex)
            out, locus = user.testMove(path, maxDist, stop, self.size, True)
            out += ability.execute(user, self.participants, locus=locus)
        else:
            if len(codex) == 0:     # No targets given
                if 'ability' in ability.targets or 'modifier' in ability.targets:
                    raise AbilityError('No targets given for a modifier- or ability-targeting ability.')
                if 'self' not in ability.targets:
                    raise AbilityError('No targets given for an ability that cannot target its user.')
                out = ability.execute(user, self.participants, targets=[user])
            else:
                targets = []
                items = []
                i = 0
                while i < len(codex):
                    name = codex[i]
                    char = self.characters[name.lower()]
                    i += 1
                    if char is user:
                        if 'self' not in ability.targets:
                            raise AbilityError('You cannot target yourself with this ability.')
                    else:
                        if 'ally' not in ability.targets and 'enemy' not in ability.targets:     # BattleBot has no way to know who is an ally and who is an enemy (yet)
                            raise AbilityError('You cannot target {} with this ability.'.format(char.name))
                    targets.append(char)
                    if 'ability' in ability.targets:
                        if codex[i].lower() in char.abilities:
                            items.append(char.abilities[codex[i].lower()])
                            i += 1
                        else:
                            items.append(choice(char.abilities))
                out = ability.execute(user, self.participants, targets=_removeDups(targets), items=_removeDups(items))
        for ch in self.participants:
            if ch.isDead() and ch not in prevDeadChars:
                self.onDeath(ch)
                #self.removeParticipantByChar(ch)
                #ch.respawn()
        if ignoreTimeout:
            ability.timeout = prevTimeout
        return out

    def useAbility(self, codex):
        if self.attacked:
            return self.availableActions()
        user = self.currentChar()
        abilityName = codex[0].lower()
        codex = codex[1:]
        try:
            out = self.useAbilityOf(user, abilityName, codex)
            self.attacked = True
            out += self.availableActions()
            if self.moved:
                self.passTurn()
        except AbilityError as e:
            return str(e)
        except KeyError as e:
            return 'Character/ability not found: {}'.format(e.args[0])
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
                        chars.append(char)
                        if tile == '  ':
                            abbrev = char.name[0:2] if not char.isMinion else char.name[-2:]
                            tile = '{:2s}'.format(abbrev)
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
