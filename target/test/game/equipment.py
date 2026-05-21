# equipment.py — 装备系统

import random
from game_data import *

QUALITY_NAMES_EQUIP = list(EQUIP_QUALITIES.keys())   # ['白','绿','蓝','紫','橙','红','彩']
SLOT_NAMES = list(EQUIP_SLOTS.keys())

class Equipment:
    def __init__(self, slot, level, quality):
        self.slot = slot          # 武器/防具/饰品/功法
        self.level = level        # 10的倍数
        self.quality = quality    # 白~彩
        self.quality_mult = EQUIP_QUALITIES[quality]
        self.stats = {}           # {属性名: 数值}
        self._generate(char_type_hint="攻击")

    def _generate(self, char_type_hint="攻击"):
        """按装备设定.md公式生成属性"""
        n = self.level
        coeff = RATE ** (n + EQUIP_LEVEL_OFFSET)
        weights = EQUIP_SLOTS[self.slot]
        feature_attr = FEATURE_ATTR.get(char_type_hint, "攻击")

        for attr_key, weight in weights.items():
            if attr_key == "特征属性":
                attr_key = feature_attr
            if attr_key not in GROWTH_BASE:
                continue
            base = GROWTH_BASE[attr_key] * (n + EQUIP_LEVEL_OFFSET) * coeff
            wave = random.uniform(*EQUIP_WAVE)
            val = int(base * wave * weight * self.quality_mult)
            if val > 0:
                if attr_key in self.stats:
                    self.stats[attr_key] += val
                else:
                    self.stats[attr_key] = val

    @staticmethod
    def random_generate(slot=None, level=10, char_type="攻击"):
        if slot is None:
            slot = random.choice(SLOT_NAMES)
        # 品质概率
        r = random.random()
        if r < 0.35: q = "白"
        elif r < 0.55: q = "绿"
        elif r < 0.72: q = "蓝"
        elif r < 0.85: q = "紫"
        elif r < 0.94: q = "橙"
        elif r < 0.98: q = "红"
        else: q = "彩"
        eq = Equipment(slot, level, q)
        eq._generate(char_type)
        return eq

    def __repr__(self):
        s = f"[{self.quality}]{self.slot} Lv{self.level} "
        s += " ".join(f"{k}+{v}" for k, v in sorted(self.stats.items()))
        return s
