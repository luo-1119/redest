# main.py v3 — 全自动战斗 + 纯ASCII网格

import random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from character import Character
from equipment import Equipment
from rune import Rune
from combat import CombatEngine, show_grid, hp_bar
from dungeon import generate_enemies, generate_rewards, THEMES

C = "\033[2J\033[H"
B = "\033[1m"
G = "\033[32m"; Y = "\033[33m"; R = "\033[31m"; CY = "\033[36m"
Z = "\033[0m"


class Game:
    def __init__(self):
        self.roster = []
        self.team = {}       # {pos:char}
        self.inv_eq = []
        self.inv_rune = []
        self.gold = 1000
        self.plv = 1         # 账号等级
        self._init()

    def _init(self):
        starters = [
            Character("炎武","攻击","A","白",1),
            Character("铁盾","防御","A","白",1),
            Character("灵心","辅助","A","白",1),
            Character("风刃","攻击","B","绿",1),
        ]
        for c in starters: c.hp_current=c.max_hp; self.roster.append(c)
        self.team = {0:starters[1], 1:starters[0], 2:starters[3], 6:starters[2]}

    def cls(self): print(C,end="")

    def head(self, title=""):
        self.cls()
        print(f"{B}{CY}╔{'═'*48}╗{Z}")
        print(f"{B}{CY}║{'天武录 v2':^46s}║{Z}")
        if title: print(f"{B}{CY}║{title:^46s}║{Z}")
        print(f"{B}{CY}╚{'═'*48}╝{Z}")
        print()

    def wait(self): input(f"\n{Y}  按回车继续...{Z}")

    # ========== 主菜单 ==========
    def main(self):
        while True:
            self.head(f"账号Lv{self.plv} | 角色{len(self.roster)} | 金币{self.gold}")
            print(f"  {B}1.{Z} 角色管理  {B}2.{Z} 编队布阵  {B}3.{Z} 装备管理")
            print(f"  {B}4.{Z} 符文管理  {B}5.{Z} 挑战副本  {B}6.{Z} 角色召唤(200金)")
            print(f"  {B}7.{Z} 设定说明  {B}0.{Z} 退出")
            c = input(f"\n  选择> ").strip()
            if c=="1": self.menu_char()
            elif c=="2": self.menu_form()
            elif c=="3": self.menu_eq()
            elif c=="4": self.menu_rune()
            elif c=="5": self.menu_dungeon()
            elif c=="6": self.summon()
            elif c=="7": self.docs()
            elif c=="0": print(f"\n  {Y}再见！{Z}"); break

    # ===== 角色 =====
    def menu_char(self):
        while True:
            self.head("角色管理")
            for i,c in enumerate(self.roster):
                pos = [k for k,v in self.team.items() if v==c]
                ps = f" [上阵:{pos[0]}]" if pos else ""
                print(f"  {i+1}. {G}{c.name:4s}{Z} {c.quality}{c.rating} {c.char_type} Lv{c.level} "
                      f"HP:{c.hp_current}/{c.max_hp}{ps}")
            print(f"\n  {B}0.{Z} 返回  输入序号查看详情")
            c = input("  > ").strip()
            if c=="0": break
            try:
                idx=int(c)-1
                if 0<=idx<len(self.roster): self._detail(self.roster[idx])
            except: pass

    def _detail(self, char):
        while True:
            self.head(f"{char.name} 详情")
            print(f"  {char.quality}{char.rating} {char.char_type} Lv{char.level}  经验:{char.exp}/{exp_to_level(char.level)}")
            print(f"  HP:{char.hp_current}/{char.max_hp} ATK:{char.atk:.0f} DEF:{char.def_:.0f}")
            print(f"  暴击:{char.crit:.0f}({char.crit_rate*100:.1f}%) 格挡:{char.block:.0f}({char.block_rate*100:.1f}%)")
            if char.ren or char.po or char.pen:
                print(f"  韧性:{char.ren} 破击:{char.po} 穿透:{char.pen}")
            print(f"  怒气:{char.rage} 技能:", ",".join(SKILLS_DB[s]["名"] for s in char.skills))
            print(f"  装备:", ",".join(f"{s}:{eq}" if eq else f"{s}:空" for s,eq in char.equipment.items()))
            print(f"  符文:", ",".join(f"槽{i+1}:{r}" if r else f"槽{i+1}:空" for i,r in enumerate(char.runes)))
            print(f"\n  {B}1.{Z}卸装备 {B}2.{Z}卸符文 {B}0.{Z}返回")
            c=input("  > ").strip()
            if c=="0": break
            elif c=="1":
                for s in char.equipment:
                    if char.equipment[s]: self.inv_eq.append(char.equipment[s]); char.equipment[s]=None
                char._recalc(); print(f"  {G}已卸{Z}"); self.wait()
            elif c=="2":
                for i in range(4):
                    if char.runes[i]: self.inv_rune.append(char.runes[i]); char.runes[i]=None
                char._recalc(); print(f"  {G}已卸{Z}"); self.wait()

    # ===== 编队 =====
    def menu_form(self):
        while True:
            self.head("编队布阵")
            gc = [self.team.get(i) for i in range(9)]
            print(show_grid(gc, [None]*9, "我方阵容"))
            print(f"\n  前排(0-2)坦克 中排(3-5)输出 后排(6-8)治疗")
            print(f"  上阵: 位置 角色序号  下阵: 位置 0  ok返回")
            c=input("  > ").strip()
            if c=="ok": break
            p=c.split()
            if len(p)==2:
                try:
                    pos=int(p[0]); idx=int(p[1])
                    if 0<=pos<=8:
                        if idx==0:
                            if pos in self.team: del self.team[pos]; print(f"  {G}下阵{Z}")
                        elif 1<=idx<=len(self.roster):
                            char=self.roster[idx-1]
                            for k,v in list(self.team.items()):
                                if v==char: del self.team[k]
                            self.team[pos]=char; char.position=pos
                            print(f"  {G}{char.name} 上阵{Z}")
                        self.wait()
                except: pass

    # ===== 装备 =====
    def menu_eq(self):
        while True:
            self.head(f"装备背包({len(self.inv_eq)})")
            for i,eq in enumerate(self.inv_eq):
                print(f"  {i+1}. {eq}")
            print(f"\n  装备: 序号 角色序号  {B}0.{Z}返回")
            c=input("  > ").strip()
            if c=="0": break
            p=c.split()
            if len(p)==2:
                try:
                    ei=int(p[0])-1; ci=int(p[1])-1
                    if 0<=ei<len(self.inv_eq) and 0<=ci<len(self.roster):
                        eq=self.inv_eq[ei]; char=self.roster[ci]
                        old=char.equip(eq.slot,eq)
                        if old: self.inv_eq.append(old)
                        self.inv_eq.pop(ei)
                        print(f"  {G}{char.name} 装备{eq}{Z}"); self.wait()
                except: pass

    # ===== 符文 =====
    def menu_rune(self):
        while True:
            self.head(f"符文背包({len(self.inv_rune)})")
            for i,r in enumerate(self.inv_rune):
                print(f"  {i+1}. {r}")
            print(f"\n  镶嵌: 序号 角色序号 槽位(1-4)  {B}0.{Z}返回")
            c=input("  > ").strip()
            if c=="0": break
            p=c.split()
            if len(p)==3:
                try:
                    ri=int(p[0])-1; ci=int(p[1])-1; sl=int(p[2])-1
                    if 0<=ri<len(self.inv_rune) and 0<=ci<len(self.roster) and 0<=sl<4:
                        r=self.inv_rune[ri]; char=self.roster[ci]
                        old=char.add_rune(sl,r)
                        if old: self.inv_rune.append(old)
                        self.inv_rune.pop(ri)
                        print(f"  {G}{char.name} 镶嵌{r}{Z}"); self.wait()
                except: pass

    # ===== 副本 =====
    def menu_dungeon(self):
        while True:
            self.head("挑战副本 (自动战斗)")
            if not self.team:
                print(f"  {R}请先编队上阵！{Z}"); self.wait(); break
            max_lv = self.plv*10
            print(f"  解锁: Lv10-{max_lv} (10的倍数)")
            print(f"  {B}1.{Z}普通  {B}2.{Z}困难  {B}3.{Z}地狱  {B}0.{Z}返回")
            c=input("  > ").strip()
            if c=="0": break
            d={"1":"普通","2":"困难","3":"地狱"}.get(c)
            if d:
                try:
                    lv=int(input(f"  副本等级(10-{max_lv})> ").strip())
                except: continue
                if lv<10 or lv>max_lv or lv%10!=0:
                    print(f"  {R}无效{Z}"); self.wait(); continue
                self._battle(lv,d)

    def _battle(self, dlv, diff):
        enemies = generate_enemies(dlv, diff)
        for pos,c in self.team.items():
            if c: c.hp_current=c.max_hp; c.rage=0; c._recalc()
        engine = CombatEngine(self.team, enemies)

        # 显示初始状态
        self.head(f"{random.choice(THEMES)} Lv{dlv} [{diff}]  战斗开始")
        print(show_grid(engine.my, engine.en, "我方 VS 敌方"))
        print()
        for c in engine.my:
            if c and c.is_alive():
                print(f"  {G}{c.name:<6}{Z} {hp_bar(c.hp_current,c.max_hp)}  ATK:{c.atk:.0f} DEF:{c.def_:.0f}")
        print(f"  {'-'*42}")
        for c in engine.en:
            if c and c.is_alive():
                print(f"  {R}{c.name:<8}{Z} {hp_bar(c.hp_current,c.max_hp)}  ATK:{c.atk:.0f} DEF:{c.def_:.0f}")
        print()

        # 全自动运行
        engine.run()

        # 显示战报
        print(f"\n  {'='*42}")
        print(f"  战斗结束! 回合数: {engine.round}")
        print(f"  {'='*42}")
        # 最近20条日志
        show_log = engine.log[-20:] if len(engine.log) > 20 else engine.log
        for msg in show_log:
            print(f"  {msg}")
        if len(engine.log) > 20:
            print(f"  ... 共 {len(engine.log)} 条战斗记录")

        # 结果
        print()
        if engine.winner == "player":
            rew = generate_rewards(dlv, diff)
            print(f"  {G}胜利! 经验+{rew['经验']}{Z}")
            for eq in rew["装备"]: self.inv_eq.append(eq); print(f"  {G}获得: {eq}{Z}")
            for r in rew["符文"]: self.inv_rune.append(r); print(f"  {G}获得: {r}{Z}")
            exp_each = rew["经验"] // max(1, sum(1 for c in self.team.values() if c))
            for pos,c in self.team.items():
                if c and c.is_alive():
                    old_lv = c.level
                    c.gain_exp(exp_each)
                    if c.level > old_lv:
                        print(f"  {Y}{c.name} 升级 Lv{old_lv}->Lv{c.level}!{Z}")
        else:
            print(f"  {R}失败...{Z}")
        self.wait()

    # ===== 召唤 =====
    def summon(self):
        if self.gold<200: print(f"  {R}金币不足！{Z}"); self.wait(); return
        self.gold-=200
        c = Character.random_create(level=max(1,self.plv*5))
        c.name+="(召)"
        self.roster.append(c)
        self.head("召唤")
        print(f"\n  {G}✨ {c}{Z}")
        self.wait()

    # ===== 说明 =====
    def docs(self):
        self.head("设定说明")
        print(f"  {B}伤害:{Z} bas*ka*kr*kf  ka=(ATK-DEF)/ATK")
        print(f"  {B}暴击:{Z} 150%  概率=暴击属性/10000  格挡=67%")
        print(f"  {B}韧性/破击:{Z} 等值抵消暴击/格挡属性")
        print(f"  {B}穿透:{Z} 无视等量防御+保底伤害")
        print(f"  {B}怒气:{Z} 普攻+33 技能-100 受伤1%/HP(上取整)")
        print(f"  {B}品质:{Z} 角色白~橙1.0~1.8  装备白~彩1.0~3.2")
        print(f"  {B}战斗:{Z} 自动模式(有怒放技能否则普攻)")
        self.wait()

if __name__ == "__main__":
    Game().main()
