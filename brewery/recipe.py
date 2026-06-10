"""
Recipe model for the Brewery Platform.

Changes in this PR
------------------
* `summary()` now includes `apparent_attenuation`.
* `total_ibu` passes `hop_utilisation_efficiency` from the new recipe field.
* Added `style_guidelines` property stub for future BeerJSON integration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .calculations import (
    calculate_abv,
    calculate_ibu,
    calculate_srm,
    calculate_apparent_attenuation,
)


@dataclass
class HopAddition:
    """A single hop addition in a recipe."""
    name: str
    alpha_acid_pct: float
    weight_oz: float
    boil_minutes: float


@dataclass
class GrainBill:
    """A single grain entry in the mash bill."""
    name: str
    weight_lbs: float
    colour_lovibond: float


@dataclass
class Recipe:
    """A complete beer recipe."""
    name: str
    batch_size_gallons: float
    original_gravity: float
    final_gravity: float
    hops: List[HopAddition] = field(default_factory=list)
    grains: List[GrainBill] = field(default_factory=list)
    hop_utilisation_efficiency: float = 1.0   # NEW: brewhouse efficiency (0-1]
    style: Optional[str] = None               # NEW: optional style tag

    # ------------------------------------------------------------------
    # Derived metrics
    # ------------------------------------------------------------------

    @property
    def abv(self) -> float:
        """Calculated ABV for this recipe."""
        return calculate_abv(self.original_gravity, self.final_gravity)

    @property
    def apparent_attenuation(self) -> float:
        """Apparent attenuation percentage."""
        return calculate_apparent_attenuation(self.original_gravity, self.final_gravity)

    @property
    def total_ibu(self) -> float:
        """Total IBU from all hop additions (Tinseth)."""
        wort_gravity = (self.original_gravity + self.final_gravity) / 2.0
        return round(
            sum(
                calculate_ibu(
                    hop.alpha_acid_pct,
                    hop.weight_oz,
                    hop.boil_minutes,
                    self.batch_size_gallons,
                    wort_gravity,
                    self.hop_utilisation_efficiency,
                )
                for hop in self.hops
            ),
            2,
        )

    @property
    def srm(self) -> float:
        """Estimated SRM colour (capped at 40)."""
        mcu = sum(
            g.weight_lbs * g.colour_lovibond / self.batch_size_gallons
            for g in self.grains
        )
        return calculate_srm(mcu)

    @property
    def style_guidelines(self) -> Optional[dict]:
        """Placeholder for future BeerJSON style-guideline integration."""
        # TODO: integrate with BeerJSON style database
        return None

    def summary(self) -> dict:
        """Return a dict of key recipe metrics."""
        return {
            "name": self.name,
            "style": self.style,
            "batch_size_gallons": self.batch_size_gallons,
            "OG": self.original_gravity,
            "FG": self.final_gravity,
            "ABV": self.abv,
            "IBU": self.total_ibu,
            "SRM": self.srm,
            "apparent_attenuation": self.apparent_attenuation,
        }
