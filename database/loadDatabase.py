def makeDB(argv):
    from database.pickleDB import Database
    import pickle
    token = ''
    _datafile = 'battlebot.pickle'
    _dev_datafile = 'battlebot_dev.pickle'

    if len(argv) > 1 and argv[1] == 'dev':
        print('Battlebot running in dev mode.')
        with open('devbot.token', mode='r') as f:
            token = f.readline().strip()
        _datafile = _dev_datafile
    else:
        print('Battlebot running in release mode.')
        with open('bot.token', mode='r') as f:
            token = f.readline().strip()
    db = Database(_datafile,pickle)
    return {'token':token,'db':db}

