class Modifier:
    """Represents a modifier, and stores all the data needed for one."""

    def getHolderMods(self):
        # print(self.holder.modifiers)
        pair = self.holder.modifiers[self.stat]
        return pair[0 if self.isMult else 1]

    def regWithHolder(self, holder=None):
        if self.holder is None:
            self.holder = holder
        if self.holder is not None:
            self.getHolderMods().append(self)

    def regWithOwner(self, owner=None):
        if self.owner is None:
            self.owner = owner
        if self.owner is not None:
            self.owner.ownedModifiers.append(self)

    def __init__(self, stat, factor=None, duration=None, isMult=None, holder=None, owner=None):
        if factor is None and duration is None and isMult is None:
            # print('The stat tuple is (in stat-factor-duration-isMult order): ' + str(stat))
            stat, factor, duration, isMult = stat   # Permit the first argument to be a tuple containing (stat, factor, duration, isMult), and ignoring the rest
        self.stat = stat.upper()
        self.factor = factor
        self.duration = duration
        self.isMult = isMult
        self.holder = holder
        self.owner = owner
        self.regWithHolder()    # No-op if holder is None
        self.regWithOwner()     # Ditto for owner

    def getOwner(self):
        return self.owner

    def getHolder(self):
        return self.holder

    def revoke(self):
        try:
            if self.holder is not None:
                self.getHolderMods().remove(self)
            if self.owner is not None:
                self.owner.ownedModifiers.remove(self)
        except (AttributeError, ValueError) as e:       # Shouldn't be needed in the future, but the database got borked in testing
            print('Something weird happened while trying to revoke a modifier:\n' + str(e))

    def verbRevoked(self):
        return 'Dispelled'

    def extend(self, amt):
        self.duration += amt
        if self.duration <= 0:
            self.revoke()
            return 0
        else:
            return self.duration

    def tick(self):
        if self.duration == 0:
            self.revoke()
        elif self.duration > 0:
            self.duration -= 1

    def __eq__(self, other):
        return self is other

    def short(self):
        if self.isMult:
            return '{:d}% {}'.format(int(self.factor * 100), self.stat)
        else:
            return '{:+d} {}'.format(self.factor, self.stat)

    def __str__(self):
        if self.isMult:
            return '{:d}% ({:d})'.format(int(self.factor * 100), self.duration)
        else:
            return '{:+d} ({:d})'.format(self.factor, self.duration)

    __repr__ = __str__
