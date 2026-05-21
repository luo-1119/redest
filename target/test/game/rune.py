# rune.py v2 — 符文比例1/2和1/6

import random
from game_data import *

RUNE_NAMES = list(RUNE_TYPES.keys())

class Rune:
    def __init__(self, rune_type, level, char_qmult=1.0):
        self.rune_type = rune_type
        self.level = level
        self.stats = {}
        self._generate(char_qmult)

    def _generate(self, char_qmult):
        n = self.level
        coeff = RATE ** n
        ratios = RUNE_TYPES[self.rune_type]
        for attr, ratio in ratios.items():
            ref = RUNE_REF_GROWTH.get(attr, attr)
            g = GROWTH_BASE.get(ref, 10)
            val = int(g * n * coeff * ratio * char_qmult)
            if val > 0:
                self.stats[attr] = val

    @staticmethod
    def random_generate(level=10, char_qmult=1.0):
        return Rune(random.choice(RUNE_NAMES), level, char_qmult)

    def __repr__(self):
        s = f"符文Lv{self.level} {self.rune_type} "
        s += " ".join(f"{k}+{v}" for k,v in sorted(self.stats.items()))
        return s
