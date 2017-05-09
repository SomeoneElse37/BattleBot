
class AbilityError(Exception):
    # An Exception class thrown when the bot is given illegal input on an ability.
    # ValueError used to be used for this purpose, but when other things threw ValueErrors, it made debugging difficult.
    pass




