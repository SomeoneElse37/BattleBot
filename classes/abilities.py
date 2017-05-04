from operator import itemgetter, attrgetter, methodcaller
from random import uniform, shuffle

from calc.vector import *
from calc.rpn import *

from classes.modifiers import *

def _pickAndRemove(candidates, n, weight):
    # print('Candidates: {!s}'.format(candidates))
    # print('Total Weight: {}'.format(weight))
    # print('Random Number: {}'.format(n))
    w = weight
    i = len(candidates) - 1
    if i < 0:
        return None
    while w > n and i >= 0:
        w -= candidates[i][0]
        i -= 1
    i += 1
    out = candidates[i]
    # print('Chose {!r}'.format(out))
    del candidates[i]
    return out

class Ability:
    """Represents an Ability that a character may call upon at any time. On their turn, at least."""

    # Ability attributes: name, range, cooldown, timeout, targets, limit, steps, flavor

    # Codex format: abilityName range cooldown ((self | ally | enemy)+ | location) [limit]
    def setFields(self, codex):
        codex = [s.lower() for s in codex]
        self.range = int(codex[0])
        self.cooldown = int(codex[1])
        self.timeout = 0
        self.targets = set()
        i = 2
        try:
            while codex[i] in {'location', 'aoe', 'random', 'self', 'ally', 'enemy', 'corpse', 'ability', 'modifier', 'reaction', 'auto'}:
                self.targets.add(codex[i])
                i += 1
            self.limit = int(codex[-1])
        except IndexError:  # No limit was given
            self.limit = 1  # so, by default, will only permit one target
        if 'aoe' in self.targets:
            self.targets.remove('aoe')
            self.targets.add('location')
        if 'location' in self.targets and not self.targets.isdisjoint({'ability', 'modifier'}):
            raise ValueError('AoE abilities cannot target abilities or modifiers (yet). Until I figure out a good way to handle that. Any ideas?')
        if 'auto' in self.targets and self.targets.isdisjoint({'self', 'random', 'location'}):
            raise ValueError('Auto abilities cannot be targeted: they must have Location/AoE, Random, or Self.')
        if self.targets.isdisjoint({'self', 'ally', 'enemy'}):
            self.targets.update({'self', 'ally', 'enemy'})

    def __init__(self, codex, owner=None):
        if codex is not None:
            self.name = codex[0]
            self.setFields(codex[1:])
        self.steps = []
        self.flavor = ''
        self.owner = owner
        self.isInUse = False

    # Creates a deep copy of the Ability object.
    # NOTE: When adding new attributes to an Ability, BE SURE to add them here!
    def copy(self, newOwner=None):
        if newOwner is None:
            newOwner = self.owner
        new = Ability(None, newOwner)
        for attrib in ['name', 'range', 'cooldown', 'timeout', 'limit', 'flavor']:
            setattr(new, attrib, getattr(self, attrib))
        for attrib in ['targets']:      # Add attributes that need to be copied to this list
            setattr(new, attrib, getattr(self, attrib).copy())
        new.steps = []
        for step in self.steps:
            nstep = step[:-1]
            nstep.append(step[-1][:])
            new.steps.append(nstep)
        return new

    def getOwner(self):
        return self.owner

    def getHolder(self):
        return self.owner

    def extend(self, amt):
        self.timeout += amt
        return self.timeout

    def revoke(self):
        self.timeout = -1

    def verbRevoked(self):
        return 'Silenced'

    def tick(self):
        if self.timeout > 0:
            self.timeout -= 1

    # Each element in steps is a list of strings. The first is always 'calc', 'condition', or 'effect'.
    # The second varies.
    #   For calc, it's the name of the variable to be calculated and assigned.
    #   For effect, it's what the effect is and who to apply it to (defaulting to 'target').
    #   For condition, it's what to compare to (defaulting to '>0'), because
    # In all cases, the above is followed by an RPN string wrapped up in a single list, describing what to calculate.
    # This method takes a codex, in slightly-more-flexible user-friendly syntax, formats it as above, and returns it.
    def parseStep(self, codex):
        out = []
        codex = [s.lower() for s in codex]
        if ':' in codex:
            i = codex.index(':')
            theRest = codex[(i+1):]
            codex = codex[:i]
        else:
            theRest = None
        # print('Codex: ' + str(codex))
        # print('The Rest: ' + str(theRest))
        if codex[0] == 'calc':
            out = codex[:2]
            codex = codex[2:]
        elif len(codex) > 1 and codex[1] == '=':
            out = ['calc', codex[0]]
            codex = codex[2:]
        elif codex[0] == 'condition':
            out = [codex[0]]
            if len(codex) <= 1:
                out.append('>0')
                codex = []
            elif codex[1] in comparisons:
                out.append(codex[1])
                codex = codex[2:]
            elif codex[1] == '=0':
                out.append('==0')
                codex = codex[2:]
            elif codex[1] == '!0':
                out.append('!=0')
                codex = codex[2:]
            else:
                out.append('>0')
                codex = codex[1:]
        elif codex[0] == 'effect':
            out = [codex[0]]
            codex = codex[1:]
            if len(codex) > 0 and codex[0] in {'redirect'}:
                out.append(codex[0])
                codex = codex[1:]
            else:
                if len(codex) > 0 and codex[0] in {'damage', 'apply', 'copy', 'cancel', 'extend'}:
                    out.append(codex[0])
                    codex = codex[1:]
                else:
                    out.append('apply')
                if len(codex) > 0 and codex[0] in {'self', 'target', 'owner', 'holder', 'source'}:
                    out.append(codex[0])
                    codex = codex[1:]
                else:
                    out.append('target')
                if 'ability' in self.targets or 'modifier' in self.targets:
                    if out[1] == 'damage' and out[2] == 'target':
                        out[1] = 'extend'
                    if out[1] == 'apply' and out[2] == 'target':
                        raise ValueError("This is an ability that targets abilities or modifiers. Applying a modifier to one of those doesn't make a whole lot of sense, now does it?")
                else:
                    if out[1] in {'cancel', 'extend'}:
                        raise ValueError("You can't cancel or extend a character. Those are for modifiers and abilities.")
                    if out[2] in {'owner', 'holder'}:
                        raise ValueError("You can't mess with the owner or holder of a character. Those are for modifiers and abilities.")
                if out[2] == 'source' and 'reaction' not in self.targets:
                    raise ValueError('Source is only for reactions.')
        else:
            raise ValueError('Invalid /editability command: {}'.format(codex[0]))

        if theRest is not None:
            out.append(theRest)
        else:
            out.append(codex)
        return out


    # Parameter to this method is the codex, straight from user input, with the keywords leading to this ability stripped off the front.
    # Will replace the Nth step if the first parameter is N; the step to calculate var if there is a step that does that; or just add the new step to the end of the list otherwise.
    def setStep(self, codex):
        cmd = codex[0].lower()
        if cmd == 'flavor':
            self.flavor = ' '.join(codex[1:])
            return
        elif cmd == 'delete':
            i = int(codex[1]) - 1
            del self.steps[i]
            return
        try:
            i = int(codex[0]) - 1
            if codex[1] == 'delete':
                del self.steps[i]
                return
            self.steps[i] = self.parseStep(codex[1:])
        except ValueError:
            name = ''
            if codex[0] == 'calc':
                name = codex[1]
            elif codex[1] == '=':
                name = codex[0]
            if name != '':
                for i, step in enumerate(self.steps):
                    if step[0] == 'calc' and step[1] == name:
                        self.steps[i] = self.parseStep(codex)
                        return
            self.steps.append(self.parseStep(codex))

    # Step format: ("calc" var | "condition" cond | "effect" ("damage" | "apply") ("self" | "target")) \[ RPN commands ... \]
    def executeInner(self, user, participants, target=None, locus=None, item=None, source=None):
        data = dict(self=user)
        if (target is None) == (item is None):
            raise RuntimeError("Mutually exclusive parameters 'target' and 'item' were either both specified or both None")
        log = ""
        if target is not None:
            data['target'] = target
            data['secrets'] = (user.secret, target.secret)
            log += 'Targeting {}:'.format(target.name)
        else:
            data['target'] = item
            data['owner'] = item.getOwner()
            data['holder'] = item.getHolder()
            data['secrets'] = (user.secret, item.getHolder().secret or item.getOwner().secret)
            log += 'Targeting {!r}:'.format(item)
        if locus is not None:
            data['locus'] = locus
        for step in self.steps:
            result, flavor = parseRPN(step[-1], data=data, functions=auxFunctions)
            if len(flavor) > 0:
                log += '\n' + flavor
            if step[0] == 'calc':
                data[step[1]] = result
            elif step[0] == 'condition':
                log += '\n{:d} {} 0: '.format(result, step[1][:-1])
                if comparisons[step[1]](result):
                    log += 'Pass'
                else:
                    log += 'Fail'
                    break
            elif step[0] == 'effect':
                if step[2] == 'target':
                    tgt = target if item is None else item
                elif step[2] == 'owner':
                    tgt = item.getOwner()
                elif step[2] == 'holder':
                    tgt = item.getHolder()
                else:
                    tgt = user
                if step[1] == 'damage':
                    dmg = int(result)
                    tgt.health -= dmg
                    tgt.health = max(tgt.health, 0)
                    log += '\nDealt {:d} damage. {} is now at {:d} health.'.format(dmg, tgt.name, tgt.health)
                elif step[1] == 'apply':
                    mod = Modifier(result, owner=user, holder=tgt)
                    log += '\n{} gets {} for {:d} turns.'.format(tgt.name, mod.short(), mod.duration)
                elif step[1] == 'extend':
                    name = repr(tgt)
                    log += "\nExtended duration or cooldown of {} to {:d} turns.".format(name, tgt.extend(result))
                elif step[1] == 'cancel':
                    log += "\n{} {!r}.".format(tgt.verbRevoked(), tgt)
                    tgt.revoke()
        return log

    def executeMiddle(self, user, participants, target=None, locus=None, item=None, source=None):
        if (target is None) == (item is None):
            raise RuntimeError("Mutually exclusive parameters 'target' and 'item' were either both specified or both None")
        if source is None:
            source = user
        char = target if item is None else item.getHolder()
        reaction = char.getReaction()
        if reaction is None:
            return self.executeInner(user, participants, target, locus, item, source)
        else:
            log = "Intercepted by {}'s {!r}!\n".format(char.name, reaction)
            log += reaction.execute(char, participants, locus=locus, source=source)
            return log + '\nEnd {!r}.'.format(reaction)

    def calcWeights(self, user, candidates):
        weights = []
        # print('Candidates: {!s}'.format(candidates))
        for target in candidates:
            # print('Calculating weight for ' + target.name)
            data = dict(self=user, target=target, secrets=(user.secret, target.secret))
            for step in self.steps:
                if step[0] == 'calc':
                    result, flavor = parseRPN(step[-1], data=data, functions=auxFunctions)
                    data[step[1]] = result
            if 'weight' in data:
                w = data['weight']
            else:
                w = 1
            weights.append((w, target))
        # print(str(weights))
        filtered = list(filter((lambda p: p[0] > 0), weights))
        # print(str(filtered))
        return sorted(filtered, key=itemgetter(0))

    def canHit(self, user, locus, char, radius):
        if char.distanceTo(locus) > radius:
            # print('{} is too far away.'.format(char.name))
            return False
        if ((char.isDead()) != ('corpse' in self.targets)):
            # print('{} is dead.'.format(char.name))
            return False
        if char is user and 'self' not in self.targets:
            # print('{} is the user.'.format(char.name))
            return False
        if char is not user and 'ally' not in self.targets and 'enemy' not in self.targets:
            # print('{} is not the user.'.format(char.name))
            return False
        return True

    def getAllTargetsInRange(self, user, participants, locus, radius):
        # targets = []
        # for char in participants:
        targets = [char for char in participants if self.canHit(user, locus, char, radius)]
        # print('Targeting {!s}'.format(targets))
        return targets

    def execute(self, user, participants, targets=None, locus=None, items=None, source=None):
        if self.timeout > 0:
            raise ValueError('This ability is on cooldown for {:d} more turns.'.format(self.timeout))
        if self.timeout < 0:
            raise ValueError('This ability is silenced.')
        self.isInUse = True
        log = ''
        if locus is not None:
            locus = Vector(locus)
        if 'random' in self.targets:
            # print('Executing randomly-targeted ability.')
            candidates = self.getAllTargetsInRange(user, participants, user.pos, self.range)
            # print('Candidate targets in range: {!s}'.format(candidates))
            candidates = self.calcWeights(user, candidates)
            # print('Weights: {!s}\n'.format(candidates))
            log += 'Weights: {!s}\n'.format(candidates)
            if self.limit < len(candidates):
                totalWeight = 0
                for weight, char in candidates:
                    totalWeight += weight
                    # print('weight + {} = {}'.format(weight, totalWeight))
                targets = []
                for i in range(self.limit):
                    w, nextTarget = _pickAndRemove(candidates, uniform(0, totalWeight), totalWeight)
                    totalWeight -= w
                    targets.append(nextTarget)
            else:
                targets = list(map(itemgetter(1), candidates))
            log += 'Targets: {!s}\n'.format(targets)
        elif 'location' in self.targets and locus is not None:
            if user.distanceTo(locus) <= self.range:
                targets = self.getAllTargetsInRange(user, participants, locus, self.limit)
                shuffle(targets)
            else:
                raise ValueError('That location is {:d} tiles away from you. This ability has a range of {:d}.'.format(user.distanceTo(locus), self.range))
        else:
            if len(targets) <= self.limit and (items is None or len(items) <= self.limit):
                for char in targets:
                    if user.distanceTo(char.pos) > self.range:
                        raise ValueError('{} is {:d} tiles away from you. This ability has a range of {:d}.'.format(char.name, user.distanceTo(char.pos), self.range))
                    if char not in participants:
                        raise ValueError('{} is not participating in this battle!'.format(char.name))
                    if char.isDead() and 'corpse' not in self.targets:
                        raise ValueError('{} is dead, and this ability cannot target corpses.'.format(char.name))
                    if not char.isDead() and 'corpse' in self.targets:
                        raise ValueError('{} is not dead, and this ability can only target corpses.'.format(char.name))
            else:
                raise ValueError('Too many targets. Requires {:d} or less; got {:d}.'.format(self.limit, len(targets)))
        if 'ability' in self.targets or 'modifier' in self.targets:
            for item in items:
                nextLog = self.executeMiddle(user, participants, item=item, locus=locus, source=source)
                log += '\n\n' + nextLog
        else:
            for char in targets:
                nextLog = self.executeMiddle(user, participants, target=char, locus=locus, source=source)
                log += '\n\n' + nextLog
        self.timeout = self.cooldown + 1
        # print(log)
        self.isInUse = False
        return log

    def __str__(self):
        out = 'Range: {:d}, Cooldown: {:d}({:d}), Targets: {!s}, Limit: {:d}'.format(self.range, self.cooldown, self.timeout, self.targets, self.limit)
        if len(self.flavor) > 0:
            out += '\n  ' + self.flavor
        for i, step in enumerate(self.steps):
            # print(str(step))
            out += '\n {:3d}: '.format(i + 1)
            # out += str(step)
            rpn = step[-1]
            step = step[:-1]
            step.append(':')
            if rpn is not None:
                step.extend(rpn)
            for cmd in step:
                out += cmd + ' '
        return out

    def __repr__(self):
        return '{} ({:d})'.format(self.name, self.timeout)

