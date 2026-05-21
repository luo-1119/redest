# game_data.py v2 — 最新父文件(2026-05-22 06:22)

RATE = 1.023293
LEVEL_CAP = 100
CRIT_RATE_DIV = 10000  # 暴击率=暴击属性/10000

# === 锚点设计.md ===
INIT = {"攻击":120,"生命":980,"防御":50,"暴击":100,"格挡":100}
GROWTH_BASE = {"攻击":12,"生命":98,"防御":5,"暴击":10,"格挡":10}

SKILL_ANCHORS = {"单体攻击":2.50,"群体攻击":1.00,"单体治疗":0.75,"群体治疗":0.50}
CRIT_DMG_MULT = 1.5      # 暴击伤害*150%
BLOCK_DMG_MULT = 1/1.5   # 格挡伤害/150%

# === 角色设计.md ===
ROLE_TYPES = {
    "攻击":{"攻击":1.05,"生命":1.0,"防御":1.0,"暴击":1.0,"格挡":1.0},
    "防御":{"攻击":1.0,"生命":1.0,"防御":1.05,"暴击":1.0,"格挡":1.0},
    "辅助":{"攻击":1.0,"生命":1.05,"防御":1.0,"暴击":1.0,"格挡":1.0},
}
RATINGS = ["B","A","S","L"]
CHAR_QUALITIES = {"白":1.0,"绿":1.1,"蓝":1.2,"紫":1.4,"橙":1.8}

def exp_to_level(n):
    """升级所需经验: (n*(n-1)/2+1)*1.023293^n"""
    return int((n*(n-1)/2+1) * (RATE**n))

# === 角色技能.md ===
SKILLS_DB = {
    "攻击A": {"名":"猛击","类型":"单体攻击","倍率":2.00,"怒气":100,"评级":"B",
              "描述":"对目标造成200%伤害"},
    "攻击B": {"名":"旋风斩","类型":"群体攻击","倍率":0.80,"怒气":100,"评级":"B",
              "描述":"对敌方全体造成80%伤害"},
    "攻击C": {"名":"暗影连弹","类型":"单体攻击","倍率":0.50,"怒气":100,"评级":"S",
              "描述":"对目标造成三次50%伤害，附加印记(每层+5%伤害/-5%受伤,上限10层,持续2回合)"},
    "防御A": {"名":"坚盾","类型":"Buff","倍率":0.25,"怒气":60,"评级":"B",
              "描述":"接下来2回合受到伤害降低25%"},
    "辅助A": {"名":"治愈","类型":"单体治疗","倍率":0.60,"怒气":80,"评级":"B",
              "描述":"为我方最虚弱目标恢复攻击60%生命"},
    "辅助B": {"名":"群体回复","类型":"群体治疗","倍率":0.40,"怒气":120,"评级":"B",
              "描述":"为我方全体恢复攻击40%生命"},
}
# 评级→可用技能映射
RATING_SKILLS = {
    "B": ["攻击A","攻击B","防御A","辅助A","辅助B"],
    "A": ["攻击A","攻击B","防御A","辅助A","辅助B"],
    "S": ["攻击C","攻击A","攻击B","防御A","辅助A","辅助B"],
    "L": ["攻击C","攻击A","攻击B","防御A","辅助A","辅助B"],
}

# === 装备设定.md ===
EQUIP_SLOTS = {
    "武器":{"攻击":1/4,"特征属性":1/4,"暴击":1/6},
    "防具":{"防御":1/4,"生命":1/4,"格挡":1/6},
    "饰品":{"攻击":1/4,"生命":1/4,"暴击":1/6},
    "功法":{"攻击":1/4,"防御":1/4,"格挡":1/6},
}
EQUIP_QUALITIES = {"白":1.0,"绿":1.1,"蓝":1.2,"紫":1.4,"橙":1.8,"红":2.4,"彩":3.2}
EQUIP_WAVE = (0.5, 1.75)
EQUIP_LEVEL_OFFSET = 5
FEATURE_ATTR = {"攻击":"攻击","防御":"防御","辅助":"生命"}

# === 宝石机制.md (比例全改为1/2, 穿透1/6) ===
RUNE_TYPES = {
    "力量符文":{"攻击":0.5,"防御":0.5},
    "体质符文":{"防御":0.5,"生命":0.5},
    "韧性符文":{"韧性":0.5},
    "破击符文":{"破击":0.5},
    "穿透符文":{"穿透":1/6},
    "暴击符文":{"暴击":0.5},
    "格挡符文":{"格挡":0.5},
}
RUNE_SLOTS_MAX = 4
RUNE_REF_GROWTH = {"韧性":"暴击","破击":"格挡","穿透":"攻击"}

# === 布局与行动.txt ===
RAGE_PER_ATTACK = 33
RAGE_SKILL_COST = 100
RAGE_PER_HP_PCT = 1
RAGE_MAX = 200
# 战斗模式: 自动释放 (满足条件放技能, 否则普攻)
AUTO_BATTLE = True

# === 属性计算 ===
def calc_growth(stat, lv, char_type="攻击", char_quality=1.0):
    g = GROWTH_BASE[stat]
    tc = ROLE_TYPES.get(char_type,{}).get(stat,1.0)
    return g * tc * char_quality * lv * (RATE**lv)

def calc_stat(stat, lv, char_type="攻击", char_quality=1.0):
    return INIT[stat] + calc_growth(stat, lv, char_type, char_quality)

def calc_damage(attacker_atk, defender_def, ratio=1.0, kr=1.0, kf=1.0, penetration=0):
    """新公式: bas*ka*kr*kf, ka=(ATK-DEF)/ATK"""
    effective_def = max(0, defender_def - penetration)
    atk_minus_def = max(1, attacker_atk - effective_def)
    ka = atk_minus_def / attacker_atk
    bas = attacker_atk * ratio
    dmg = bas * ka * kr * kf
    return max(1, int(dmg))

def calc_eff_crit(atk_crit, def_ren):
    return max(0, atk_crit - def_ren)

def calc_eff_block(def_block, atk_po):
    return max(0, def_block - atk_po)

# 常用等级经验表
def gen_exp_table(max_lv=30):
    return {n:exp_to_level(n) for n in range(1,max_lv+1)}
