# combat.py v3 — 纯ASCII网格 + 全自动战斗

import random
from game_data import *

TARGET_PRIORITY = {
    0:[0,1,2,3,4,5,6,7,8], 1:[1,0,2,4,3,5,7,6,8], 2:[2,1,0,5,4,3,8,7,6],
    3:[3,4,5,0,1,2,6,7,8], 4:[4,3,5,1,0,2,7,6,8], 5:[5,4,3,2,1,0,8,7,6],
    6:[6,7,8,0,1,2,3,4,5], 7:[7,6,8,1,0,2,4,3,5], 8:[8,7,6,2,1,0,5,4,3],
}

def _front(team): return [i for i in [0,1,2] if team[i] and team[i].is_alive()]
def _mid(team):   return [i for i in [3,4,5] if team[i] and team[i].is_alive()]
def _back(team):  return [i for i in [6,7,8] if team[i] and team[i].is_alive()]

def find_target(pos, enemy_team):
    pri = TARGET_PRIORITY.get(pos, list(range(9)))
    allowed = set(_front(enemy_team) or _mid(enemy_team) or _back(enemy_team) or [])
    for p in pri:
        if p in allowed: return p
    return None

def show_grid(my, en, title="战斗"):
    """纯ASCII网格，兼容dict和list"""
    def get(tm, i):
        if isinstance(tm, dict): return tm.get(i)
        return tm[i] if i < len(tm) else None
    def cell(tm, i):
        c = get(tm, i)
        return c.name[:4].ljust(4) if (c and c.is_alive()) else "····"
    rows = []
    rows.append(f"  +----+----+----+----+----+----+")
    rows.append(f"  |         {title:^16s}         |")
    rows.append(f"  +----+----+----+----+----+----+")
    rows.append(f"  |后左|后中|后右|后左|后中|后右|")
    rows.append(f"  +----+----+----+----+----+----+")
    for my_row, en_row in [([6,3,0],[0,3,6]),([7,4,1],[1,4,7]),([8,5,2],[2,5,8])]:
        cells = [cell(my,i) for i in my_row] + [cell(en,i) for i in en_row]
        rows.append(f"  |" + "|".join(cells) + "|")
        rows.append(f"  +----+----+----+----+----+----+")
    return "\n".join(rows)

def hp_bar(cur, mx, w=10):
    if mx <= 0: return "[" + "░"*w + "] 0/0"
    pct = cur/mx
    f = max(1, int(pct*w)) if pct > 0 else 0
    return "[" + "█"*f + "░"*(w-f) + f"] {cur}/{mx}"

class CombatEngine:
    def __init__(self, my_team_dict, enemy_list):
        self.my = [None]*9; self.en = [None]*9
        for pos,c in my_team_dict.items():
            self.my[pos]=c; c.position=pos
        for i,c in enumerate(enemy_list):
            if i<9 and c: self.en[i]=c; c.position=i
        self.round=0; self.log=[]; self.winner=None

    def run(self):
        while self.winner is None:
            self.round += 1
            for idx in range(9):
                mc=self.my[idx]; ec=self.en[idx]
                if mc and mc.is_alive() and ec and ec.is_alive():
                    if (mc.atk+mc.def_) >= (ec.atk+ec.def_):
                        self._act(mc,self.en); self._check()
                        if self.winner: return
                        self._act(ec,self.my); self._check()
                        if self.winner: return
                    else:
                        self._act(ec,self.my); self._check()
                        if self.winner: return
                        self._act(mc,self.en); self._check()
                        if self.winner: return
                elif mc and mc.is_alive():
                    self._act(mc,self.en); self._check()
                    if self.winner: return
                elif ec and ec.is_alive():
                    self._act(ec,self.my); self._check()
                    if self.winner: return
            for team in [self.my, self.en]:
                for c in team:
                    if c and c.is_alive():
                        for k in list(c.buffs.keys()):
                            c.buffs[k]-=1
                            if c.buffs[k]<=0: del c.buffs[k]
                        for k in list(c.marks.keys()):
                            c.marks[k]["turns"]-=1
                            if c.marks[k]["turns"]<=0: del c.marks[k]
                        c._recalc()

    def _act(self, actor, enemy_team):
        sid = actor.best_skill()
        if sid: self._skill(actor, sid, enemy_team)
        else: self._normal(actor, enemy_team)

    def _normal(self, actor, enemy_team):
        tpos = find_target(actor.position, enemy_team)
        if tpos is None: return
        t = enemy_team[tpos]
        if not t or not t.is_alive(): return
        dmg = self._dmg(actor, t, 1.0)
        a = t.take_damage(dmg)
        actor.rage_gain_attack()
        t.rage_gain_hurt(a)
        self.log.append(f"  {actor.name} -> {t.name}  -{a}")
        if not t.is_alive(): self.log.append(f"  X {t.name}")

    def _skill(self, actor, sid, enemy_team):
        info = SKILLS_DB[sid]
        actor.rage -= info["怒气"]
        st = info["类型"]; r = info["倍率"]; nm = info["名"]
        if st == "单体攻击":
            tpos = find_target(actor.position, enemy_team)
            if tpos is None: return
            t = enemy_team[tpos]
            if not t or not t.is_alive(): return
            n = 3 if sid=="攻击C" else 1; td = 0
            for _ in range(n):
                d = self._dmg(actor, t, r)
                a = t.take_damage(d); td += a
                t.rage_gain_hurt(a)
            self.log.append(f"  {actor.name}[{nm}] -> {t.name}  -{td}")
            if sid=="攻击C":
                m = t.marks.setdefault(actor.name,{"stacks":0,"turns":2})
                m["stacks"] = min(10, m["stacks"]+1)
                m["turns"] = 2
            if not t.is_alive(): self.log.append(f"  X {t.name}")
        elif st == "群体攻击":
            for t in enemy_team:
                if t and t.is_alive():
                    d = self._dmg(actor, t, r)
                    a = t.take_damage(d)
                    t.rage_gain_hurt(a)
                    self.log.append(f"  {actor.name}[{nm}] -> {t.name}  -{a}")
                    if not t.is_alive(): self.log.append(f"  X {t.name}")
        elif st == "单体治疗":
            allies = [c for c in self.my if c and c.is_alive()]
            if allies:
                t = min(allies, key=lambda c: c.hp_current)
                a = t.heal(actor.atk*r)
                self.log.append(f"  {actor.name}[{nm}] -> {t.name}  +{a}")
        elif st == "群体治疗":
            for c in self.my:
                if c and c.is_alive():
                    a = c.heal(actor.atk*r)
                    self.log.append(f"  {actor.name}[{nm}] -> {c.name}  +{a}")
        elif st == "Buff" and sid=="防御A":
            actor.buffs["减伤Buff"] = 2
            actor._recalc()
            self.log.append(f"  {actor.name}[{nm}] 减伤25% 2T")

    def _dmg(self, atker, defer, ratio):
        eff_c = calc_eff_crit(atker.crit, defer.ren)
        eff_b = calc_eff_block(defer.block, atker.po)
        cr = min(1.0, eff_c/CRIT_RATE_DIV)
        br = min(1.0, eff_b/CRIT_RATE_DIV)
        is_c = random.random() < cr
        is_b = random.random() < br
        kr = CRIT_DMG_MULT if is_c else 1.0
        kf = BLOCK_DMG_MULT if is_b else 1.0
        mk = 1.0
        if atker.name in defer.marks:
            mk = 1.0 + defer.marks[atker.name]["stacks"]*0.05
        d = calc_damage(atker.atk, defer.def_, ratio, kr*kf*mk, 1.0, atker.pen)
        if is_c: self.log.append("    !暴击")
        if is_b: self.log.append("    !格挡")
        return d

    def _check(self):
        if not any(c and c.is_alive() for c in self.my): self.winner="enemy"
        if not any(c and c.is_alive() for c in self.en): self.winner="player"
