# dungeon.py v2

import random
from character import Character
from equipment import Equipment
from rune import Rune

THEMES = ["试炼之塔","暗影洞穴","龙息荒原","灵泉秘境","魔渊裂隙","古战场"]
PREFIX = ["魔化","暗影","狂怒","精英","远古","混沌"]

def generate_enemies(dungeon_lv, difficulty="普通"):
    diff = {"普通":1.0,"困难":1.3,"地狱":1.6}[difficulty]
    team = []
    for i in range(9):
        lv = max(1, int(dungeon_lv*diff))
        c = Character.random_create(level=lv)
        if i<3 and c.char_type!="防御":
            c.char_type="防御"; c._recalc()
        c.name = random.choice(PREFIX)+c.name
        c.hp_current = c.max_hp
        team.append(c)
    return team

def generate_rewards(dungeon_lv, difficulty="普通"):
    rew = {"装备":[],"符文":[],"经验":0}
    ec = {"普通":1,"困难":2,"地狱":3}[difficulty]
    rc = {"普通":0,"困难":1,"地狱":2}[difficulty]
    elv = max(10,(dungeon_lv//10)*10)
    for _ in range(ec):
        rew["装备"].append(Equipment.random_generate(level=elv))
    for _ in range(rc):
        rew["符文"].append(Rune.random_generate(level=elv))
    rew["经验"] = dungeon_lv*50*{"普通":1,"困难":2,"地狱":3}[difficulty]
    return rew
