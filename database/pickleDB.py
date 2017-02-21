from classes.battles import Battle
from classes.abilities import Ability

#This file contains everything to interact with the pickle version of the database

_CURRENT_DB_VERSION = 18

def _updateDBFormat(database):
    if 'version' not in database or database['version'] < _CURRENT_DB_VERSION:
        print("Updating database format.")
        for k, v in database.items():
            if k != 'version':
                # Battle attributes: characters, participants, turn, id, name, radius
                # Ex:
                # if not hasattr(v, 'moved'):
                #     v.moved = False
                if hasattr(v, 'orphanModifiers'):
                    for mod in v.orphanModifiers:
                        mod.revoke()
                    delattr(v, 'orphanModifiers')

                for l, w in v.characters.items():
                    # Character attributes: username, userid, name, race, size, statPoints, baseStats, abilities, modifiers, health, location, secret
                    if not hasattr(w, 'ephemeral'):
                        w.ephemeral = False
                    if not hasattr(w,"isMinion"):
                        w.isMinion=True
                        w.minionCount=0 #this tracks how often a minion has been made using this character as its base
                        w.forceTurnSkip=False
                    # for m, x in w.abilities.items():
                        # Ability attributes: name, range, cooldown, timeout, targets, limit, steps, flavor
        database['version'] = _CURRENT_DB_VERSION

class Database:
    def __init__(self, fileName, pickle):
        self.fileName=fileName
        self.pickle=pickle
        try:
            with open(fileName, 'rb') as f:
                self.db = pickle.load(f)
            _updateDBFormat(self.db)
            print(str(len(self.db) - 1) + ' guilds loaded.')
        except FileNotFoundError:
            print('Database could not be loaded. Creating an empty database.')
            self.db={}

    def exitDB(self):
        with open(self.fileName, 'wb') as f:
            self.pickle.dump(self.db, f, self.pickle.HIGHEST_PROTOCOL)
        print('Database saved to disk.')

    def getBattle(self, serverId):
        # print(type(self.db))
        # print(str(serverId))
        # print(repr(serverId))
        return self.db[serverId]

    def createGuild(self, guild):
        if self.guildExists(guild):
            raise ValueError(guild.name + 'is already known to Battlebot!')
        else:
            self.db[guild.id]=Battle(guild)#makeBattle(guild.id, Battle(guild))

    def guildExists(self, guild):
        return guild in self.db

    def getAllCharacters(self, serverId):
        return self.db[serverId].characters

    def getCharacter(self, serverId, charName):
        battle = self.getBattle(serverId)
        return battle.characters[charName.lower()]

    def insertCharacter(self, server, char):
        if not self.guildExists(server):
            self.createGuild(server)
        self.db[server.id].addCharacter(char)

    def toggleSecretChar(self, serverId, charName):
        char = self.getCharacter(serverId, charName)
        char.secret = not char.secret
        return char

    def updateStats(self, serverId, charName, stats, overwriteBattleLock=False):
        battle = self.getBattle(serverId)
        char = self.getCharacter(charName)
        if char not in battle.participants or isGM:
            char.statPoints = stats
            return str(char) + '\n\n{:d} stat points used.'.format(sum(char.statPoints.values()))
        return False

    def updateHealth(self, serverId, charName, newHealth):
        char = self.getCharacter(serverId, charName)
        char.health = newHealth
        return char

    def respawnChar(self, serverId, charName):
        char = self.getCharacter(serverId, charName)
        char.respawn()
        return char

    def updateLocation(self, serverId, charName, newX, newY):
        char = self.getCharacter(serverId, charName)
        char.pos = int(newX), int(newY)
        return str(char)

    def updateSize(self, serverId, newX, newY):
        battle = self.getBattle(serverId)
        battle.size = (newX, newY)
        return str(battle)

    def insertAbility(self, serverId, codex, overwriteBattleLock=False):
        battle = self.getBattle(serverId)
        char = self.getCharacter(serverId, codex[0].lower())
        if char not in battle.participants or overwriteBattleLock:
            try:
                abl = char.abilities[codex[1].lower()]
                abl.setFields(codex[2:])
                return str(abl)
            except KeyError:
                abl = Ability(codex[1:])
                char.abilities[abl.name.lower()] = abl
                return str(abl)
        return False

    def updateAbility(self, serverId, codex, overwriteBattleLock=False):
        battle = self.getBattle(serverId)
        char = self.getCharacter(serverId, codex[0].lower())
        if char not in battle.participants or overwriteBattleLock:
            abl = char.abilities[codex[1].lower()]
            abl.setStep(codex[2:])
            return str(abl)
        return False

    def getAbilities(self, serverId, charName):
        char = self.getCharacter(serverId, charName)
        return char.listAbilities()

    def deleteChar(self, battleId, charName):
        battle = self.getBattle(battleId)
        battle.delete(charName)

    def guildExists(self, guild):
        return guild.id in self.db

    def getCurrentChar(self, serverId):
        battle = self.getBattle(serverId)
        return battle.currentChar()

    def makeBattle(self, guild, battle):
         self.db[guild.id] = battle

    def doPassTurn(self, serverId):
        battle = self.getBattle(serverId)
        battle.passTurn()
        return battle.currentCharPretty()

    def doBasicAttack(self, target, serverId):
        battle= self.getBattle(serverId)
        return battle.basicAttack(target) + '\n\n' + battle.currentCharPretty()

    def doMove(self, codex, serverId):
        battle = self.getBattle(serverId)
        return battle.move(codex) + '\n\n' + battle.currentCharPretty()

    def doAbility(self, codex, serverId):
        battle = self.getBattle(serverId)
        return battle.useAbility(codex) + '\n\n' + battle.currentCharPretty()

    def clearBattle(self, battleId):
        battle = self.getBattle(battleId)
        battle.clear()

    def addParticipant(self, charName, battleId):
        battle = self.getBattle(battleId)
        battle.addParticipant(charName)
        return charName + ' has successfully joined the battle!'
    def minionByChar(self,charName,battleId,forcedPassTurn):
        character = self.getCharacter(battleId,charName)
        battle = self.getBattle(battleId)
        minion = character.minionFy(battle,forcedPassTurn)
        return minion
    def getModifiers(self, serverId, charName):
        char = self.getCharacter(serverId, charName)
        return char.listModifiers()

    def toggleTurnSkip(self,charName,serverId):
        char = self.getCharacter(charName,serverId)
        char.forceTurnSkip = not char.forceTurnSkip
        return char.forceTurnSkip

