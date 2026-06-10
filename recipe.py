"""
recipe.py
Recipe builder and batch scaling utilities.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class HopAddition:
    name: str
    weight_grams: float
    alpha_acid_pct: float
    boil_minutes: float


@dataclass
class GrainBill:
    name: str
    weight_kg: float
    colour_lovibond: float


@dataclass
class Recipe:
    name: str
    batch_litres: float
    original_gravity: float
    final_gravity: float
    hops: List[HopAddition] = field(default_factory=list)
    grains: List[GrainBill] = field(default_factory=list)

    def scale(self, new_batch_litres: float) -> "Recipe":
        """Return a new Recipe scaled to a different batch size."""
        if new_batch_litres <= 0:
            raise ValueError("Target batch size must be positive.")
        factor = new_batch_litres / self.batch_litres
        scaled_hops = [
            HopAddition(
                h.name, round(h.weight_grams * factor, 2),
                h.alpha_acid_pct, h.boil_minutes
            )
            for h in self.hops
        ]
        scaled_grains = [
            GrainBill(g.name, round(g.weight_kg * factor, 2), g.colour_lovibond)
            for g in self.grains
        ]
        return Recipe(
            name=self.name,
            batch_litres=new_batch_litres,
            original_gravity=self.original_gravity,
            final_gravity=self.final_gravity,
            hops=scaled_hops,
            grains=scaled_grains,
        )
