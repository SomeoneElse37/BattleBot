from random import uniform

from calc.vector import *
from calc.rpn import *

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
            while codex[i] in {'location', 'aoe', 'random', 'self', 'ally', 'enemy', 'corpse', 'ability', 'modifier', 'reaction'}:
                self.targets.add(codex[i])
                i += 1
            self.limit = int(codex[-1])
        except IndexError:  # No limit was given
            self.limit = 1  # so, by default, will only permit one target
        if 'aoe' in self.targets:
            self.targets.remove('aoe')
            self.targets.add('location')

    def __init__(self, codex):
        self.name = codex[0]
        self.setFields(codex[1:])
        self.steps = []
        self.flavor = ''

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
        elif codex[1] == '=':
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
            if len(codex) > 0 and codex[0] in {'extend', 'cancel', 'steal', 'redirect'}:
                out.append(codex[0])
                codex = codex[1:]
            else:
                if len(codex) > 0 and codex[0] in {'damage', 'apply'}:
                    out.append(codex[0])
                    codex = codex[1:]
                else:
                    out.append('apply')
                if len(codex) > 0 and codex[0] in {'self', 'target'}:
                    out.append(codex[0])
                    codex = codex[1:]
                else:
                    out.append('target')
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
    def executeInner(self, user, target, locus=None):
        data = dict(self=user, target=target, secrets=(user.secret, target.secret))
        log = 'Targeting {}:'.format(target.name)
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
                char = target if step[2] == 'target' else user
                if step[1] == 'damage':
                    char.health -= result
                    char.health = max(char.health, 0)
                    log += '\nDealt {:d} damage. {} is now at {:d} health.'.format(result, char.name, char.health)
                else:
                    mod = Modifier(result, owner=user, holder=char)
                    log += '\n{} gets {} for {:d} turns.'.format(char.name, mod.short(), mod.duration)
        return log

    def calcWeights(self, user, candidates):
        weights = []
        for target in candidates:
            data = dict(self=user, target=target, secrets=(user.secret, target.secret))
            for step in self.steps:
                if step[0] == 'calc':
                    result, flavor = parseRPN(step[-1], data=data, functions=auxFunctions)
                    data[step[1]] = result
                weights.append(data['weight'], target)
        return weights.sort()

    def canHit(self, user, locus, char):
        if char.distanceTo(locus) > self.limit:
            return False
        if ((char.isDead()) != ('corpse' in self.targets)):
            return False
        if char is user and 'self' not in self.targets:
            return False
        if char is not user and 'ally' not in self.targets and 'enemy' not in self.targets:
            return False
        return True

    def getAllTargetsInRange(self, user, participants, locus):
        targets = [char for char in participants if self.canHit(user, locus, char)]
        shuffle(targets)
        return targets

    def pickAndRemove(candidates, n, weight):
        w = weight
        i = len(candidates) - 1
        if i < 0:
            return None
        while w > n and i >= 0:
            w -= candidates[i][0]
            i -= 1
        i += 1
        out = candidates[i]
        del candidates[i]
        return out

    def execute(self, user, participants, targets=None, locus=None):
        if self.timeout > 0:
            raise ValueError('This ability is on cooldown for {:d} more turns.'.format(self.timeout))
        if 'random' in self.targets:
            candidates = getAllTargetsInRange(user, participants, user.pos)
            if self.limit < len(candidates):
                self.calcWeights(user, candidates)
                totalWeight = 0
                for weight, char in candidates:
                    totalWeight += weight
                targets = set()
                for i in range(self.limit):
                    w, nextTarget = pickAndRemove(candidates, uniform(0, weight), weight)
                    totalWeight -= w
                    targets.add(nextTarget)
            else:
                targets = set(candidates)
        elif locus is not None:
            if user.distanceTo(locus) <= self.range:
                targets = getAllTargetsInRange(user, participants, locus)
            else:
                raise ValueError('That location is {:d} tiles away from you. This ability has a range of {:d}.'.format(user.distanceTo(locus), self.range))
        else:
            if len(targets) <= self.limit:
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
        log = ''
        for char in targets:
            nextLog = self.executeInner(user, char, locus)
            log += '\n\n' + nextLog
        self.timeout = self.cooldown + 1
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

