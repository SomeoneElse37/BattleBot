help_dict = {'bot': """Welcome to BattleBot!
This is a Discord bot written by Someone Else 37 using discord.py.
It rolls dice and things, and has a multitude of commands useful for anyone GMing a role-play using the
combat system lenscas and I developed for ANWA. It is based off the combat system used in BtNS and ABG.
In fact, BattleBot can just about handle all of the mechanics of an ANWA RP on its own. Just add flavor.
Or, at least, it will once it's complete. Battlebot is a work in progress.

Battlebot kind of grew out of an simple dicebot written by Eruantien. Much thanks to him for getting me started.

For more info on how to use BattleBot, type /help contents

Want to add BattleBot to your server? Type /invite
\*Note, this may not actually give you a functional invite link. I'm not sure why.

Want to host BattleBot yourself, look at the sourcecode, or file a bug report? Type /github

**Note: Many of these help pages are quite long. Please do not use them outside of your server's designated spam channel, or the GM (and the other players) will be very annoyed with you.**""",
        'contents': """Table of Contents

/help bot: General bot information
/help contents: View this page again
/help player: Useful commands for players in an RP
/help battle: Commands for use during a battle
/help move: Detailed information on the /move command
/help move2: /move, page 2
/help map: Detailed information on the /map command
/help stats: How stats work in BattleBot
/help modifier: How stat modifiers (i.e. buffs and debuffs) work
/help ability: Deailed information on abilities and how to create them
/help ability2: Ability Parameters
/help ability3: The /editability command
/help ability4: A Shocking Example
/help rpn: Crash course on Reverse Polish Notation
/help rpn2: Details on BattleBot's take on RPN
/help rpn3: RPN operators only useful in abilities
/help gm: Commands for GMs
/help calc: Commands that roll dice and calculate stuff. Mostly obsoleted by all the above.

**Note: Many of these help pages are quite long. Please do not use them outside of your server's designated spam channel, or the GM (and the other players) will be very annoyed with you.**""",
        'player': """Player Commands
These commands are usable by all players, and do not typically have any impact on the state of the battle.

/roll XdY: Roll X dYs and add the results.
/defaultstats: Print out the default stats for all the size tiers.
/makechar name race [hp acc eva atk dfn spd]: Create a character with the given name, race, and stat point distribution.
    Accepted races: faerie, elf, human, werecat, elfcat, cyborg, robot, kraken, elfship, steamship
/restat name hp acc eva atk dfn spd: Reshuffle your stats. Only works outside of battle.
/delete name: Delete a character. Only works on characters you created. Warning, this is permanent!
/join name: Join the battle ongoing on your server.
    Support for using /join with no argument to automatically add one of your characters is planned, but NYI.
/list: List a bunch of info about the current state of the battle- who's participating, turn order, etc.
/list name: Show all the info about the named character.
/modifiers name: Show all modifiers on the named character.
/abilities name: Show all of the abilities the named character has.
/send name serverName: Send a clone of the named character to the named server.
/send name serverID [newName]: As above, but by server ID, optionally with a new name (to resolve naming conflicts).
    The copy will be owned and controlled by you, not necessarily its original owner.
/invite: Show BattleBot's invite link.
/github: Show the link to this bot's sourcecode on GitHub.""",
        'battle': """Battle Commands
These commands are to be used during battle, and can only be used by the active player or a GM. See /help gm for more info.

/attack name: Punch the named character with a basic physical attack.
    This and the next few commands only work during your turn.
/move ...: Move along the specified path, as far as your speed roll allows.
    See /help move for info on the path syntax.
/ability abilityName [name ... | path]: Use an ability on the given targets, at the location at the end of the path, or on yourself if no targets or path are given.
    Path syntax is exactly the same as in /move.
/pass: Pass your turn. Simple enough.

Note: During their turn, the active player may use both /move AND either /attack or /ability, if they wish (although they cannot use /attack and /ability in the same turn).""",
        'move': """The /move Command
This command allows players to move about the battlefield. Its syntax is quite flexible and powerful, if a bit complex.

The simplest way to use /move is to simply give it a pair of NS/WE coordinates. Example:
/move 5N 3E
will move the character along a straight line to a point at most 5 units north and 3 units east of their current position.
Henceforth, I will call this bit of syntax a "direction". The coordinates can be specified in any order, and lowercase letters work fine.
You can even leave out the NS or WE coordinate entirely. /move 3s means "go 3 units due south".
Furthermore, if you leave out the distance component, it will default to 1. /move N means "go one tile north".

Alternatively, you can type out the name of any character in the battle in place of coordinates, and BattleBot
will interpret that as "go straight toward the location of the named character." It's actually treated as a
direction internally, and I will use that term interchangably to refer to both.

Type /help move2 to continue reading""",
        'move2': """The full argument format of /move is this:
/move direction [direction | + direction | - dist] ... [+ | dist]
Remember, you can use names as waypoints in place of directions.
Essentially, it takes a list of directions (and waypoints), and the character will follow that path as far as the speed roll permits.

Placing a + sign between two directions will cause them to be added together, and the character will perform both at once by traveling a straight line. Example:
/move lenscas + 2E
will be interpreted as "go two tiles to the east of lenscas".

Following a direction by a - sign, then an integer distance, will cause the character to stop short of where the previous direction command would've taken them, by no more than the specified distance in tiles. If you've got an ability with a maximum range of 16, for instance, you can type
/move lenscas - 16
to move just within range.

The list of directions can also be suffixed with either a + sign or an integral distance.
/move 2N 1S 5E +
means "move 2 tiles north, then in the direction of 1S 5E, and keep going in that direction as far as the speed roll permits."

If the last argument is an integer, it means "move no more than this many tiles, continuing past the end of the path in the direction of the last segment if necessary."
/move N E 25
will be interpreted as "move northeast as far as possible, up to 25 tiles." """,
        'map': """The /map Command

/map, well, draws a map of the battlefield. It, too, is very flexible, though not nearly as complex as /move.
The default size of the map is 26x26. This nicely fits within a Discord post.

/map: if given no arguments, map the entire battlefield, scaled to fit within a single post.
/map scale: draw the whole battlefield, using the specified scale factor. Bigger numbers yield a smaller, more zoomed-out map.
/map x y: draw a map of the default size centered on the given location, with scale factor 1 (i.e. 1 map tile = 1 grid tile)
/map x y radius: draw a map of the given size centered on the given point, with scale factor 1.
/map xMin xMax yMin yMax: draw a map covering the given area
/map xMin xMax yMin yMax scale: draw a map covering the given area, with the given scale factor. Again, bigger scale factor = more zoomed-out map.

The map will show characters with the first two letters in their name. If two characters exist in the same tile, BattleBot will use a number instead and display a legend showing who all is represented by each number.

I plan to have /map automatically give a view of the most interesting area of the battlefield eventually, but I'm not quite entirely sure how to do that. Any ideas?""",
        'stats': """Stats and How They Work

Battlebot's stat system is a bit complex, so I thought I ought to explain it here. Each character has six different stats:
HP: Health points. Basically how much damage you can take before you die.
ACC: Accuracy. The more of this you have, the more likely you'll actually be able to land an attack.
EVA: Evasion. The more of this you have, the better your chances of dodging an attack and taking no damage at all.
ATK: Attack. How hard you hit.
DEF: Defense. How well you are able to resist being hit.
SPD: Speed. Determines order of initiative and how quickly you can move around the battlefield.

In addition, there are four different ways the word "stat" can be used:
Species Stats: The "base" stats shared by all members of a species. Currently, these are
    shared across *size tiers*, not just species. See /calc defaultstats for details.
Stat Points: These are specific to each individual. Players are given a GM-specified number
    of these to distribute across their six stats as they choose.
Unmodified Stats: The results of combining the Species Stats and Stat points, calculated as
    UnmodifiedStat = SpeciesStat \* (1 + (StatPoints / 8)). See below.
Effective Stats: The result of applying modifiers to the Unmodified Stats. See /help modifier for details.

Each point allocated to a stat increases the unmodified stat from the base species stat by *one eighth of that species stat*.

For instance, werecats have 16 species HP. A werecat with 0 points allocated to HP will have, well, 16 HP.
    No points allocated = no change in the stat.
A werecat with one point in HP will have 16 \* (1 + 1 / 8) = 18 HP.
A werecat with 4 points in HP will have 16 \* (1 + 4 / 8) = 24 HP.

Allocating 4 points will multiply the species stat by 1.5, and allocating 8 points will double it. It's pretty linear.""",
        'modifier': """Modifiers

Battlebot supports modifiers to stats, of the multiplicative and additive varieties.
When computing a character's effective stats, BattleBot first computer their unmodified stats as described in /help stats.
Then, BattleBot multiplies together all the character's multiplicative modifiers on each stat, and does the same for the additive modifiers.
The effective stats are computed as follows:
EffectiveStat = floor(UnmodifiedStat \* MultiplicativeModifiers + AdditiveModifiers)

Each modifier has the following data:
    Stat: Which stat the modifier, well, modifies.
    Strength: The amount by which the modifier modifies its associated stat.
    Duration: How long the modifier will last.
    Holder: The character to which the modifier applies.
    Owner: The character who created the modifier.

The durations of all modifiers tick down at the end of the turn of their *owner*. When the modifier's duration drops below zero, it is removed entirely.
Thus, a modifier with duration 0 will vanish at the end of its creator's next turn (or current turn, if it is currently their turn).
A newly-created modifier with duration N is guaranteed to last exactly N full turn cycles, barring ability shenenigans.

Also note that modifiers whose durations are already negative will never decay. They are only cleared at the end of a battle (again, barring ability shenanigans).

Also, modifiers instantly vanish the moment their owner dies. Because otherwise, modifiers whose creators died would never expire, and that would be weird.
Unless they have no owner, which is also possible to do.""",
        'ability': """Abilities

BattleBot's ability system uses four commands.
/ability abilityName [targets | path]: Use an ability. An ability that is still on cooldown cannot be used
        until the cooldown expires; but otherwise, the restrictions on this are the same as for /attack.
    If it's a targeted ability, you can give it a list of targets. If none are given, targets yourself by default.
    If it's an AoE ability, give it a path to where you want the effect to be focused.
            The path syntax is exactly the same as that described in /help move.
/abilities name: List all of that character's abilities.
/makeability name abilityName range cooldown targetTypes [limit]: Create an ability, or change these fields
        of an ability that already exists.
    name: The name of the character that will have this ability.
    abilityName: The name of the ability.
    range: The maximum permissible distance between you and your target(s).
    cooldown: How many turns this ability will not be available after using it.
        Cooldown 1 means that you will not be able to use the ability again for one turn after using it
                (so you can use it every other turn).
        Cooldown 0 is no cooldown.
    parameters: A description of what kinds of things the ability is able to target. See /help ability2.
    limit: For AoE abilities, the radius of the affected area. For targeted abilities, the maximum number of targets.
            Deaults to 1.
/editability: See /help ability3""",
        'ability2': """Ability Parameters

This argument to /makeability consists of a list of any number of the following words, separated by spaces. There are very few restrictions on which ones or how many can be used together: want your ability to target a random modifier or ability on a random allied corpse? Sure!

location: This is an AoE ability, to be aimed at a location on the grid.
aoe: Alias for location.
self: Can target the user.
ally: Can target the user's teammates.
enemy: Can target the user's opponents.
    Note: As BattleBot does not handle teams (yet), ally and enemy are synonymous.
corpse: Can target characters that are dead, but not those that are living.
ability: Can target other abilities, but not characters. Incompatible with location/AoE.
modifier: Can target modifiers, but not characters. Incompatible with location/AoE.
random: Chooses its targets at random from all characters in range, without requiring ANY input from the user.
    If the ability computes a variable called 'weight' (see 'calc var' in /help ability3), that number is used
    to weight the random number generator. Larger weights are more likely to be chosen.
reaction: This ability triggers in response to the user being targeted with another ability. Cannot be activated directly
    using /ability. May be used to redirect the ability to its source or to one or more other characters. Implies 'random'
    and uses this ability's range, limit, and parameters to choose the new targets (if the ability is actually redirected).""",
        'ability3': """The /editability Command

/editability name abilityName [N] action [:] rpn ...: Edits the sequence of steps that the ability performs for each target.
    N: If given, replace line n rather than appending step n to the end of the list.
    action: What this step of the ability is supposed to do. Can take any one of the following formats:
        calc var: Executes the RPN expression, and stores its result in a variable called var for use in later steps.
            If the ability already has a step to calculate var, replace that step.
        var =: Same as calc var. Yes, that has to be a single equals sign.
        condition [cmp]: Compare the RPN result to 0 in one of six ways. If false, then stop execution
                of the ability right then and there and start over with the next target.
            Possible values of cmp are: <0, =0, ==0, >0, <=0, !0, !=0, >=0. If none are given, default to >0.
        effect [damage | apply] [self | target]: An effect of this ability.
            damage: Deal damage to a character. Does not roll dice, so use one of the roll commands in /help rpn2.
            apply: Apply a modifier to a character. The RPN expression must return a modifier: see /help rpn3.
                Defaults to apply if neither are given.
            self: The effect applies to the user of the ability, regardless of who the target may be.
                    Useful for recoil damage.
            target: The effect applies to the target.
                Defaults to target if neither are given.
        flavor: Set the ability's flavor text.
        N delete | delete N: Delete step N from the ability.
    :  The colon is optional. If specified, it separates the action from the RPN string unambiguously.
    rpn: The last parameter to /editability must be an RPN expression. It is executed whenever the ability is used,
            and its return value determines what will happen. See /rpn for details.

Type /help ability4 for an example.""",
        'ability4': """A Shocking Example

Say you've got a character named "Zeus", and you want him to be able to summon lightning. You could type the following commands in this order:

/makeability zeus Smite 100 2 aoe 5
/editability zeus smite flavor Call down a bolt of lightning from the sky that will damage everyone within 5 tiles with up to 3x strengh, tapering off the farther they are away from the center of the strike.
/editability zeus smite dst = locus target pos dist
/editability zeus smite power = self atk 5 dst - * 3 * 5 //
/editability zeus smite effect damage power target def rolldmg

Now, you can use
/abilities Zeus
to have BattleBot return all of the above information to you.
If it's Zeus's turn to make a move,
/ability smite 6N
will use it on anyone and everyone within 11 tiles North of you.""",
        'rpn': """Reverse Polish Notation

RPN is a way to write mathematical formulae and such. It will seem a bit strange to anyone used to the familiar infix notation, but is very easy for computers to understand.
RPN is a *postfix* notation, meaning that all operators come *after* the things they operate on. For example:
/calc rpn 2 3 4 + 5 - *
The interpreter will read this string with the help of a stack. Whenever it encounters a number, it will push that number onto the stack. After reading the 2, the stack will look like this:
`[2]`
Then, after the 3 and 4 are read:
`[2, 3, 4]`
Note that I'm showing the top of the stack as the rightmost end of this list.
Most operators, including + and *, will pop *two* values off the stack, operate on them, and push the result back onto the stack.
Upon reading the + sign, the interpreter will pop the 4 and 3 off the stack, add them to get 7, and push the 7 back onto the stack. The stack now looks like this:
`[2, 7]`
Next comes the 5.
`[2, 7, 5]`
The - sign will pop the 5 and 7. 7-5=2:
`[2, 2]`
And, finally, * will multiply the 2s.
`[4]`
The input has been exhausted, and the stack has only one element. That whole formula thus evaluates to 4.
And indeed, 2 * ((3 + 4) - 5) = 4.

RPN allows math formulae to be written in a perfectly unambiguous manner that is very easy to parse. It's quite nice.

Type /help rpn2 for more details on exactly what operations BattleBot's RPN parser can perform.""",
        'rpn2': """BattleBot RPN

BattleBot's RPN parser has a number of operations that it can perform. First, the basics. These operators all pop two numbers off the stack, and push their result back on.
+ : Addition. Pretty simple.
- : Subtraction. Note that the second number popped is the number the other is subtracted *from*- so "5 1 -" means the same thing as "5 - 1" equals 4. Not -4.
        All the operators that take multiple arguments work this way. The first number pushed goes on the left hand side of the operator.
* : Multiplies the two numbers. Simple.
/ : Division. May return a floating-point number: "5 2 /" evaluates to 2.5.
//: Floor division. Divides, then rounds down (i.e. toward -infinity). "5 2 //" evaluates to 2.

The rest of these have English names, and are not case-sensitive.
sum: Add together ALL the numbers on the stack, and push the result back on as the only element in the stack.
        So "1 2 3 4 5 sum" returns 15.

roll: Takes one argument off the stack. Roll that namy d10s, and push the sum back on the stack.
rollh: Like roll, except hide the individual rolls. Just return the sum.
rollu: As above, but hide the rolls if the user's stats are secret.
rollt: As above, but use the target's secret status.
rollacc: Perform an accuracy check. Take two arguments and roll that many d10s.
calcdmg: If the two arguments are 50 and 20, return how much damage would be dealt if I rolled a 50 and you rolled a 20.
rolldmg: Roll the two arguments, then call calcdmg on the results.

All of the above commands are available to /calc rpn, so try them out yourself.
For the RPN commands that really only make sense in the context of an ability, type /help rpn3.""",
        'rpn3': """RPN Ability Commands

First off, you should be aware that the RPN parser can handle several different types of values. Integers are parsed as, well, integers; anything that doesn't parse as an integer or match any of the operators will be parsed as a string; and some of the operators can return more complex objects.

These first few aren't operators, per se, as they take no arguments at all.
self: The actual Character using this ability. Intended to be followed by one of the commands in the next section.
target: The character targeted by this ability.
locus: For an AOE ability, the location where the effect is centered. Not available otherwise.

These all take one argument, extected to be a character (so... self or target).
hp: The *maximum* HP of the character.
acc: The Accuracy stat of the character. All modifiers and whatnot are properly taken into account.
eva: Evasion stat.
atk: Attack.
def: Defense.
spd: Speed.
health: The character's *current* HP.
pos: The character's position.

Next, the modifier operators. All take three arguments, of the form [factor, stat, duration]. They do not affect anything right away, but the returned object can be applied to a character later on in the ability.
They are +mod, -mod, mod%, +mod%, and -mod%. The syntax parallels that of /addModifier, described in /help gm. So I'll just give some examples in the RPN format here:
    10 ATK 3 +mod == +10 Strength for 3 turns
    5 EVA 2 -mod == -5 Evasion for 2 turns
    150 SPD 0 mod% == 150% Speed until end of turn
    20 DEF 1 +mod% == +20% (== 120%) Defense for 1 turn
    15 ACC -1 -mod% == -15% (== 85%) Accuracy until end of battle

And finally, with two arguments,
dist: The Pythagorean straight-line distance between two locations (as returned by locus or pos). May be used to have the effect of an ability depend on the distance between the user and the target, or on the distance between the target and the epicenter of an AOE effect, etc. Go wild.""",
        'gm': """GM commands
These commands/behaviors only function if you are a GM, meaning that you have either Administrator or Manage Messages permission on the server.

/pass, /attack, /delete, etc: GMs can use these commands to control or mess with other players' characters.
    GMs can also /restat characters that are currently partaking in a battle.
/clear: Clear the current battle and heal and respawn all participants.
/addModifier name [+|-]factor[%] stat duration owner: Added a modifier to the named character.
    If the % is omitted, create an additive multiplier that increases the stat by the specified amount (or dereases it, if negative).
    If the % is present. what happens depends on the sign given, if any.
        Plus sign means "increase this stat by the specified pecentage"
        Minus sign means "decrease this stat by the specified percentage"
        No sign means "set this stat to this percentage of what is was before"
    So 120% and +20% mean the same thing, as do 80% and -20%.
    Acceptable stats are HP, ACC, EVA, ATK, DEF, and SPD. All are case-insensitive.
/warp name x y: Teleports the named character to the given coordinates.
/sethp name [health]: Sets the named character's current health, or to their maximum health is none is specified.
/togglesecret name: Toggle whether the named character's stats are hidden from players.
/gmattack name acc atk [secret?]: Perform at attack with the given Accuracy and Attack against the named character.
    If 0 or a negative number is specified for acc or atk, those stats will not be rolled.
    If anything at all is given for the fourth parameter, the bot will not echo the Accuracy or Attack specified.
    It's up to you to delete/edit your post to prevent players from reading the stats from it.
/setsize x y: Set the size of the battlefield to (x, y).
/excel: Generate an ODF spreadsheet of... something. I'm not sure what.""",
        'calc': """Calculation Commands
These just roll dice and calculate stuff. They have no effect on the battle at all.

/calc roll XdY: Roll X dYs and add the results. Alias of /roll.
/calc check acc eva: Roll a BtNS-style accuracy check.
/calc damage atk def: Do a damage roll in my fancy BtNS-inspired way.
/calc avgdmg atk def: Do 1000 damage rolls, calculate a bunch of summary statistics, and produce a histogram.
   Each `#` in the histogram represents 10 rolls that dealt that amount of damage, `|` is 5, `:` is 2, and `.` is 1
/calc attack acc atk eva def hp: Roll accuracy and damage repeatedly, until HP damage has been dealt.
/calc repattack acc atk eva def hp: Run /attack many times over, then return summary statistics and a histogram.
/calc range r: Convert a range integer into a human-readable string.
/calc rangedump: Generate a list of all the range ranges, and their names.
/calc rangelookup strn: Look up the given range string, and return the range integers that it corresponds to.
    Only requires that the given name be a substring of the name in BattleBot's sourcecode, and ignores case:
    /calc rangelookup ortBOW works fine.
/calc approach r spd [r2]: Do an approach roll, approaching the melee circle or, optionally, another character at range r2.
/calc retreat r spd: Do a retreat roll.
/calc defaultstats: Print out the default stats for all the size tiers. Alias of /defaultstats.
/calc testStatRoll n bucketSize: Test my new statical dice-rolling code against the count-and-add code by rolling n d10s.
    Returns a histogram. Each row is a bucket of bucketSize, collecting all rolls from one algorithm within its range.
    The even-numbered rows correspond to the count-and-add algorithm; the odd ones to the new statistical algorithm.
/calc rpn ...: Invoke BattleBot's RPN parser. Type /help rpn for more info."""}

for k, v in help_dict.items():
    if len(v) > 2000:
        print('Warning: /help {:s} is {:d} characters long! Max message length is 2000!'.format(k, len(v)))


