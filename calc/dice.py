# All of the dice-rolling functions are here. ALL OF THEM.
# All the ones that don't do a whole lot else, at least.

def d10(times, sides):
    dice_list = []
    for foo in range(0, times):
        bar = randint(1, sides)
        dice_list += [bar]
    return(dice_list)

def formatRoll(rolls):
    return(str(sum(rolls)) + ' = ' + str(rolls))

def roll(codex):
    codex = codex[0].split('d')
    return(formatRoll(d10(int(codex[0]), int(codex[1]))))

# Emulates rolling n d10s and adding the results by way of the Gaussian function above, and returns the simulated sum.
# Th weird constants and stuff come from the Central Limit Theorem. Go look it up, if you're so inclined.
def statisticD10Sum(n):
    return max(0, round(gauss(5.5, math.sqrt(8.25) / math.sqrt(n)) * n))

# Rolls N d10s and returns the result. If N <= 300, will call d10() and formatRoll(), literally rolling a bunch of virtual d10s.
# If N > 300, will instead use statistical methods to simulate rolling the dice, to save on CPU time and message length.
# if given secret=True as a parameter, will not report the number of dice rolled.
# In any case, returns a pair, (log, sum) of the sum of the dice rolled and a human-readable log of the rolls themselves
def prettyRoll(n, secret=False):
    if not secret:
        if n <= 100:
            rolls = d10(n, 10)
            return formatRoll(rolls), sum(rolls)
        else:
            roll = statisticD10Sum(n)
            return '{:d} = [... x{:d} ...]'.format(roll, n), roll
    else:
        roll = 0                    # The Central Limit Theorem really kicks in with a sample size >= 30,
        if n <= 30:                 # if the underlying distribution is not heavily skewed.
            roll = sum(d10(n, 10))  # Hence why I use 30 here.
        else:
            roll = statisticD10Sum(n)
        return '{:d} = [...]'.format(roll), roll

accCheckFlavors = [
        'The attack missed by a mile.',
        'Failure. The attack missed.',
        'Success! The attack connects.',
        'Critical hit? Maybe?'
        ]

aglCheckFlavors = [
        'No. Not even close.',
        "Couldn't quite escape melee range.",
        'Just made it out of melee range.',
        'Easily escaped melee range.'
        ]

def checkString(r1, r2, flavors=accCheckFlavors):
    diff = r1 - r2
    if diff < -20:
        return flavors[0]
    elif diff <= 0:
        return flavors[1]
    elif diff <= 20:
        return flavors[2]
    else:
        return flavors[3]

def formatCheck(atk, dfn):
    r1 = sum(atk)
    r2 = sum(dfn)
    diff = r1 - r2
    out = formatRoll(atk) + '\n' + formatRoll(dfn) + '\n'
    return out + checkString(r1, r2)

def check(codex):
    return formatCheck(d10(int(codex[0]), 10), d10(int(codex[1]), 10))

# Rolls an accuracy check, using modern dice-rolling and secret-handling technology. Optional keyword argument called secrets
# takes a pair of booleans, defaulting to (False, False). If secrets[0] is True, the number of Accuracy dice rolled will not be reported;
# if secrets[1] is true, the number of Evasion dice will not be reported.
def prettyCheck(acc, eva, secrets=(False, False), flavors=accCheckFlavors):
    s1, r1 = prettyRoll(acc, secrets[0])
    s2, r2 = prettyRoll(eva, secrets[1])
    return s1 + '\n' + s2 + '\n' + checkString(r1, r2, flavors=flavors), r1 > r2

# Used in the command that rolls damage a bunch of times. Yes, I'm duplicating code, sue me.
def calcDamage(atk, dfn):   # Takes the attack and defense STATS as parameters (not rolls)
    r1 = sum(d10(atk, 10))
    r2 = sum(d10(dfn, 10))
    ratio = r1 / r2
    return math.ceil(ratio - 1)

def damageString(r1, r2):
    ratio = r1 / r2
    dmg = max(math.ceil(ratio - 1), 0)
    out = "{:d}%: ".format(int(ratio * 100))
    if dmg == 0:
        return out + "The attack was blocked.", 0
    else:
        return out + "The attacker dealt " + str(dmg) + " damage.", dmg

def formatDamage(atk, dfn):
    r1 = sum(atk)
    r2 = sum(dfn)
    out = formatRoll(atk) + '\n' + formatRoll(dfn) + '\n'
    dmgstr, dmg = damageString(r1, r2)
    return out + dmgstr, dmg

def damage(codex):
    return(formatDamage(d10(int(codex[0]), 10), d10(int(codex[1]), 10))[0])

def prettyDamage(atk, dfn, secrets=(False, False)):
    s1, r1 = prettyRoll(atk, secrets[0])
    s2, r2 = prettyRoll(dfn, secrets[1])
    dmgstr, dmg = damageString(r1, r2)


