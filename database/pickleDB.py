_CURRENT_DB_VERSION = 15
from classes.battles  import Battle
#This file contains everything to interact with the pickle version of the database
def _updateDBFormat(database):
    if 'version' not in database or database['version'] < _CURRENT_DB_VERSION:
        print("Updating database format.")
        database['version'] = _CURRENT_DB_VERSION
#        for k, v in database.items():
#            if k != 'version':
#                # Battle attributes: characters, participants, turn, id, name, radius
#                # Ex:
#                # if not hasattr(v, 'moved'):
#                #     v.moved = False

#                for l, w in v.characters.items():
#                    # Character attributes: username, userid, name, race, size, statPoints, baseStats, abilities, modifiers, health, location, secret
#                    # Ex:
#                    # if not hasattr(w, 'abilities'):
#                    #     w.abilities = []

#                    ##### This is where CHARACTER attributes get added! BATTLE attributes go above and an indent level to the left! Stop forgetting that, SE!


class Database:
    
    def __init__(self,fileName,pickle):
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

    def getBattle(self,serverId):
        print(type(self.db))
        return self.db[serverId]
    def createGuild(self,guild):
        if self.guildExists(guild):
            raise ValueError(guild.name + 'is already known to Battlebot!')
        else:
            self.db[guild.id]=Battle(guild)#makeBattle(guild.id,Battle(guild))
    def guildExists(self,guild):
        return guild in self.db
    def getAllCharacters(self,serverId):
        return self.db[serverId].characters
    def getCharacter(self,serverId,charName):
        battle =self.getBattle(serverId)
        return battle.characters[charName.lower()]
    def insertCharacter(self,server,char):
        if not self.guildExists(server):
            self.createGuild(server)
        self.db[server.id].addCharacter(char)
        
    def toggleSecretChar(self,serverId,charName):
        char = self.getCharacter(serverId,charName)
        char.secret = not char.secret
        return char
    
    def updateStats(self,serverId,charName,stats,overwriteBattleLock=False):
        battle = self.getBattle(serverId)
        char = self.getCharacter(charName)
        if char not in battle.participants or isGM:
            char.statPoints = stats
            return str(char) + '\n\n{:d} stat points used.'.format(sum(char.statPoints.values()))
        return False
    def updateHealth(self,serverId,charName,newHealth):
        char = self.getCharacter(serverId,charName)
        char.health = newHealth
        return char
    def respawnChar(self,serverId,charName):
        char = self.getCharacter(serverId,charName)
        char.respawn()
        return char
    def updateLocation(self,serverId,charName,newX,newY):
        char = self.getCharacter(serverId,charName)
        char.pos = int(newX),int(newY)
        return str(char)
    def insertAbility(self,serverId,codex,overwriteBattleLock=False):
        battle = self.getBattle(serverId)
        char  = self.getCharacter(codex[0].lower())
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
    def updateAbility(self,serverId,codex,overwriteBattleLock=False):
        char = self.getCharacter(codex[0].lower())
        battle = self.getBattle(serverId)
        if char not in battle.participants or overwriteBattleLock:
            abl = char.abilities[codex[1].lower()]
            abl.setStep(codex[2:])
            return str(abl)
        return False
    def getAbilities(self,serverId,charName):
        char = self.getCharacter(serverId,charName)
        return char.listAbilities()
    def deleteChar(self,battleId,charName):
        battle= self.getBattle(battleId)
        battle.deleteChar(charName)
        
    def guildExists(self,guild):
        return guild.id in self.db
        
    def getCurrentChar(self,serverId):
        battle = self.getBattle(serverId)
        return battle.currentChar()
    
    def makeBattle(self,guild,battle):
         self.db[guild.id] = battle
         
    def doPassTurn(self,serverId):
        battle = self.getBattle(serverId)
        battle.passTurn()
        return battle.currentCharPretty()
    
    def doBasicAttack(self,target,serverId):
        battle= self.getBattle(serverId)
        return battle.basicAttack(target) + '\n\n' + battle.currentCharPretty()
        
    def doMove(self,codex,serverId):
        battle = self.getBattle(serverId)
        return battle.move(codex) + '\n\n' + battle.currentCharPretty()
        
    def doAbility(self,codex,serverId):
        battle = self.getBattle(serverId)
        return battle.useAbility(codex) + '\n\n' + battle.currentCharPretty()
        
    def clearBattle(self,battleId):
        battle = self.getBattle(battleId)
        battle.clear()
    
    def addParticipant(self,charName,battleId):
        battle = self.getBattle(battleId)
        battle.addParticipant(charName)
        return charName + ' has successfully joined the battle!'
        
    def getModifiers(self,serverId,charName):
        char = self.getCharacter(serverId,charName)
        return char.listModifiers()
