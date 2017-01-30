_CURRENT_DB_VERSION = 15

#This file contains everything to interact with the pickle version of the database
def _updateDBFormat(database):
    if 'version' not in database or database['version'] < _CURRENT_DB_VERSION:
        print("Updating database format.")
        database['version'] = CURRENT_DB_VERSION
        for k, v in database.items():
            if k != 'version':
                # Battle attributes: characters, participants, turn, id, name, radius
                # Ex:
                # if not hasattr(v, 'moved'):
                #     v.moved = False

                for l, w in v.characters.items():
                    # Character attributes: username, userid, name, race, size, statPoints, baseStats, abilities, modifiers, health, location, secret
                    # Ex:
                    # if not hasattr(w, 'abilities'):
                    #     w.abilities = []

                    ##### This is where CHARACTER attributes get added! BATTLE attributes go above and an indent level to the left! Stop forgetting that, SE!


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
