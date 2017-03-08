import math

from calc.dice import *
from calc.vector import *

def _sumThings(xs, data):
    total = sum(xs)
    return [total], '{:d} = {!s}'.format(total, xs)

def _flip(pair):
    # print('##### Flipping {!s} #####'.format(pair))
    a, b = pair
    return [b], a

def _wrap(fn):
    return lambda xs, data: ([fn(xs[0])], '')

def _rollAccCheckForRPN(xs, data):
    log, hit = prettyCheck(xs[0], xs[1], data['secrets'])
    return [(1 if hit else 0)], log

# Any data that parseRPN() could be expected to be able to look up from the beginning
# By default, considers both "characters'" stats to be visible (because they don't really have stats to hide)
baseData = {'secrets': (False, False),
        'pi': math.pi,
        'e': math.e}

# Operators and functions that parseRPN should have access to, even without any character context
baseFunctions = {'+': (2, lambda xs, data: ([xs[0] + xs[1]], '')),
        '-': (2, lambda xs, data: ([xs[0] - xs[1]], '')),
        '*': (2, lambda xs, data: ([xs[0] * xs[1]], '')),
        '@': (2, lambda xs, data: ([xs[0] @ xs[1]], '')),
        '/': (2, lambda xs, data: ([xs[0] / xs[1]], '')),
        '//': (2, lambda xs, data: ([int(xs[0] // xs[1])], '')),
        'sum': (-1, _sumThings),
        'abs': (1, _wrap(abs)),
        'sqrt': (1, _wrap(math.sqrt)),
        'sin': (1, _wrap(math.sin)),
        'cos': (1, _wrap(math.cos)),
        'tan': (1, _wrap(math.tan)),
        'asin': (1, _wrap(math.asin)),
        'acos': (1, _wrap(math.acos)),
        'atan': (1, _wrap(math.atan)),
        'atan2': (1, lambda xs, data: ([xs[0].atan2()], '')),
        'dot': (2, lambda xs, data: ([xs[0] * xs[1]], '')),
        'cross': (2, lambda xs, data: ([xs[0] @ xs[1]], '')),
        'dist': (2, lambda xs, data: ([abs(xs[0] - xs[1])], '')),
        'vec': (2, lambda xs, data: ([Vector((xs[0], xs[1]))], '')),
        'coords': (1, lambda xs, data: (xs[0].coords, '')),                             # Vector.coords returns a tuple, which is iterable, so it should work in List.extend()
        'roll': (1, lambda xs, data: _flip(prettyRoll(xs[0]))),                         # Rolls some d10s. Simple enough.
        'rollh': (1, lambda xs, data: _flip(prettyRoll(xs[0], True))),                  # Rolls some d10s, but hides the actual rolls.
        'rollu': (1, lambda xs, data: _flip(prettyRoll(xs[0], data['secrets'][0]))),    # Hides the actual rolls if and only if the user's stats are hidden.
        'rollt': (1, lambda xs, data: _flip(prettyRoll(xs[0], data['secrets'][1]))),    # Hides the actual rolls if and only if the target's stats are hidden.
        'rollacc': (2, _rollAccCheckForRPN),
        'calcdmg': (2, lambda xs, data: _flip(damageString(xs[0], xs[1]))),
        'rolldmg': (2, lambda xs, data: _flip(prettyDamage(xs[0], xs[1], data['secrets'])))}

# Parses an RPN codex, with the specified context. data and functions will be merged with baseData and baseFunctions,
# with the data and functions having precedence if any of the keys conflict.
def parseRPN(codex, data = {}, functions = {}):
    codex = [s.lower() for s in codex]
    data = {**baseData, **data}
    functions = {**baseFunctions, **functions}
    stack = []
    log = ''
    try:
        for op in codex:
            try:
                stack.append(int(op))
            except ValueError:
                if op in data:
                    stack.append(data[op])
                elif op in functions:
                    args, fn = functions[op]
                    par = []
                    if args >= 0:
                        for i in range(args):
                            par.append(stack.pop())
                            par = par[::-1]
                    else:
                        par = stack
                        stack = []
                    retvals, note = fn(par, data)
                    stack.extend(retvals)
                    if len(note) > 0:
                        log += '\n' + note
                else:
                    log += '\nUnrecognized operator:' + op
    except (IndexError, TypeError) as e:
        raise RuntimeError('There was an error!', e, log, stack)
    if len(stack) == 1:
        return stack[0], log
    else:
        # log += '\n\nWarning: Expected stack to contain exactly one item after execution; got {!s}'.format(stack)
        return stack, log

def testRPN(codex):
    retval, log = parseRPN(codex)
    return log + '\n\n' + str(retval)

# Used in the auxFunctions list to get a stat from an object, and format the result as parseRPN expects.
# Unless the object isn't a character, in which case just return the object and the stat.
# This would be so much easier in Haskell, where I don't need to go so far out of my way to curry functions with if statements in them...
def getstat(stat, alt, xs):
    try:
        return [getattr(xs[0], alt)()]
    except AttributeError:
        return [xs[0], stat]

def statgetter(stat, alt=None):
    if alt is None:
        alt = stat
    return lambda xs, data: (getstat(stat, alt, xs), '')

# These functions are formatted the same way as baseFunctions, but are aimed for use in abilities.
auxFunctions = {
        'hp':  (1, statgetter('hp')),
        'acc': (1, statgetter('acc')),
        'eva': (1, statgetter('eva')),
        'atk': (1, statgetter('atk')),
        'def': (1, statgetter('def', 'dfn')),
        'spd': (1, statgetter('spd')),
        'health': (1, lambda xs, data: ([xs[0].health], '')),
        'pos': (1, lambda xs, data: ([xs[0].pos], '')),
        '+mod': (3, lambda xs, data: ([(xs[2], xs[0], xs[1], False)], '')),
        '-mod': (3, lambda xs, data: ([(xs[2], -xs[0], xs[1], False)], '')),
        'mod%': (3, lambda xs, data: ([(xs[2], xs[0] / 100, xs[1], True)], '')),
        '+mod%': (3, lambda xs, data: ([(xs[2], 1 + xs[0] / 100, xs[1], True)], '')),
        '-mod%': (3, lambda xs, data: ([(xs[2], 1 - xs[0] / 100, xs[1], True)], ''))}
# stat, factor, duration, isMult
comparisons = {
        '<0': lambda n: n < 0,
        '==0': lambda n: n == 0,
        '>0': lambda n: n > 0,
        '<=0': lambda n: n <= 0,
        '!=0': lambda n: n != 0,
        '>=0': lambda n: n >= 0}

