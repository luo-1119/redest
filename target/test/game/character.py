# character.py v2 — 角色系统(新增经验升级)

import random
from game_data import *

FIRST_NAMES = ["炎","冰","雷","风","光","暗","铁","灵","玄","幽","烈","霜","影","星","龙"]
LAST_NAMES = ["武","姬","魂","刃","盾","心","皇","王","尊","仙"]

class Character:
    def __init__(self, name, char_type, rating, quality, level=1):
        self.name = name
        self.char_type = char_type
        self.rating = rating
        self.quality = quality
        self.qmult = CHAR_QUALITIES[quality]
        self.level = level
        self.exp = 0
        self.equipment = {s:None for s in EQUIP_SLOTS}
        self.runes = [None]*RUNE_SLOTS_MAX
        self.rage = 0
        self.hp_current = 0
        self.buffs = {}       # {name: turns_left}
        self.marks = {}       # {target_name: {stacks, turns}} 印记系统(攻击C)
        self.position = None
        self.skills = self._pick_skills()
        self._recalc()

    def _pick_skills(self):
        """按角色类型和评级从技能库选技能"""
        t = self.char_type
        pool = RATING_SKILLS.get(self.rating, RATING_SKILLS["B"])
        my = []
        for sid in pool:
            info = SKILLS_DB[sid]
            # 类型匹配
            if t == "攻击" and info["类型"] in ("单体攻击","群体攻击"):
                my.append(sid)
            elif t == "防御" and info["类型"] in ("Buff",):
                my.append(sid)
            elif t == "辅助" and info["类型"] in ("单体治疗","群体治疗"):
                my.append(sid)
        # 至少给一个
        if not my:
            if t == "攻击": my = ["攻击A"]
            elif t == "防御": my = ["防御A"]
            else: my = ["辅助A"]
        return my[:3]  # 最多3个技能

    def _recalc(self):
        q = self.qmult; t = self.char_type; lv = self.level
        for s in ["攻击","生命","防御","暴击","格挡"]:
            setattr(self, s, calc_stat(s, lv, t, q))
        self.ren = 0; self.po = 0; self.pen = 0
        # 装备
        for eq in self.equipment.values():
            if eq:
                for k,v in eq.stats.items():
                    if hasattr(self,k): setattr(self,k,getattr(self,k)+v)
        # 符文
        for r in self.runes:
            if r:
                for k,v in r.stats.items():
                    if hasattr(self,k): setattr(self,k,getattr(self,k)+v)
        # Buff
        if "攻Buff" in self.buffs:
            self.攻击 *= (1+self.buffs["攻Buff"])
        if "防Buff" in self.buffs:
            self.防御 *= (1+self.buffs["防Buff"])
        if "减伤Buff" in self.buffs:
            self._dmg_reduce = self.buffs["减伤Buff"]
        else:
            self._dmg_reduce = 0
        # 衍生
        self.crit_rate = min(1.0, self.暴击/CRIT_RATE_DIV)
        self.block_rate = min(1.0, self.格挡/CRIT_RATE_DIV)
        self.max_hp = int(self.生命)
        if self.hp_current<=0 or self.hp_current>self.max_hp:
            self.hp_current = self.max_hp

    # 为兼容性保留别名
    @property
    def atk(self): return self.攻击
    @property
    def def_(self): return self.防御
    @property
    def crit(self): return self.暴击
    @property
    def block(self): return self.格挡

    def equip(self, slot, equipment):
        old = self.equipment[slot]
        self.equipment[slot] = equipment
        self._recalc()
        return old

    def add_rune(self, idx, rune):
        if 0<=idx<RUNE_SLOTS_MAX:
            old = self.runes[idx]
            self.runes[idx] = rune
            self._recalc()
            return old

    def gain_exp(self, amount):
        self.exp += amount
        while self.level < LEVEL_CAP:
            need = exp_to_level(self.level)
            if self.exp >= need:
                self.exp -= need
                self.level += 1
                self._recalc()
                self.hp_current = self.max_hp
            else:
                break

    def take_damage(self, dmg):
        dmg = max(0,int(dmg*(1-self._dmg_reduce)))
        self.hp_current = max(0, self.hp_current - dmg)
        return dmg

    def heal(self, amount):
        old = self.hp_current
        self.hp_current = min(self.max_hp, self.hp_current+int(amount))
        return self.hp_current-old

    def is_alive(self):
        return self.hp_current > 0

    def rage_gain_attack(self):
        self.rage = min(RAGE_MAX, self.rage+RAGE_PER_ATTACK)

    def rage_gain_hurt(self, dmg):
        pct = dmg/self.max_hp*100
        gain = max(1, int(pct+0.999))  # 向上取整
        self.rage = min(RAGE_MAX, self.rage+gain)

    def can_skill(self, sid=None):
        """检查技能是否可用(有足够怒气)"""
        if sid is None:
            return any(self.can_skill(s) for s in self.skills)
        if sid not in self.skills: return False
        return self.rage >= SKILLS_DB[sid]["怒气"]

    def best_skill(self):
        """返回最佳可用技能(怒气足够的第一优先)"""
        for s in self.skills:
            if self.can_skill(s):
                return s
        return None

    def __repr__(self):
        pct = self.hp_current/self.max_hp*100
        sk = ",".join(SKILLS_DB[s]["名"] for s in self.skills)
        return (f"{self.quality}{self.rating} {self.char_type} Lv{self.level} "
                f"HP:{self.hp_current}/{self.max_hp}({pct:.0f}%) "
                f"ATK:{self.atk:.0f} DEF:{self.def_:.0f} 怒:{self.rage} [{sk}]")

    @staticmethod
    def random_create(level=1, name=None):
        if name is None:
            name = random.choice(FIRST_NAMES)+random.choice(LAST_NAMES)
        t = random.choice(list(ROLE_TYPES.keys()))
        r = random.random()
        if r<0.50: q="白"
        elif r<0.75: q="绿"
        elif r<0.90: q="蓝"
        elif r<0.98: q="紫"
        else: q="橙"
        r2 = random.random()
        if r2<0.40: rating="B"
        elif r2<0.75: rating="A"
        elif r2<0.95: rating="S"
        else: rating="L"
        c = Character(name,t,rating,q,level)
        c.hp_current=c.max_hp
        return c
