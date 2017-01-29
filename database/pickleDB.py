_CURRENT_DB_VERSION = 14

#This file contains everything to interact with the pickle version of the database
def _updateDBFormat(database):
    if 'version' not in database or database['version'] < _CURRENT_DB_VERSION:
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
            self.pickle.dump(database, f, self.pickle.HIGHEST_PROTOCOL)
        print('Database saved to disk.')

    def getBattle(self,author):
        return self.db[author.server.id]

    def getCharacter(self,author,charName):
        battle =self.getBattle(author)
        return battle[charName.lower()]

    def insertCharacter(self,server,char):
        if not self.guildExists(author.server):
            self.createGuild(server)
        self.db[server.id].addCharacter(char)
    def deleteChar(self,authorId,charName):
        battle= self.getBattle(authorId)
        battle.deleteChar(charName)
    def guildExists(self,guild):
        return guild.id in self.db

    def makeBattle(self,guild,battle)
         self.db[guild.id] = battle
    
    def clearBattle(self,battleId):
        self.db[author.server.id].clear()
    def addParticipant(self,user):
        battle = self.getBattle(user)
        battle.addParticipant(user)
        return user + ' has successfully joined the battle!'
    def getModifiers(self,serverId,charName):
        char = self.getCharacter(serverId,charName)
        return char.listModifiers()
