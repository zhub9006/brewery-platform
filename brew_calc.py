"""
brew_calc.py  (refactored)
Core brewing calculations for the Brewery Platform.

Changes in this PR
------------------
* ABV: switched from simplified (OG-FG)*131.25 to the more accurate
  Miller / Alternate formula that accounts for non-linear attenuation.
* IBU: added a volume-correction factor for evaporation loss.
* calculate_srm: now accepts an optional `volume_gal` and `weight_lb`
  directly so callers no longer have to pre-compute MCU.
* apparent_attenuation: allow FG == OG (0 % attenuation) as a valid
  degenerate case instead of raising.
* priming_sugar_grams: switched CO2 factor from 2.0 → 4.0 (claimed
  "fix" for metric/imperial unit mix-up — needs review).

Formulas reference:
  ABV  : alternately ((76.08*(OG-FG)/(1.775-OG)) * (FG/0.794))
  IBU  : Tinseth (with evaporation correction)
  SRM  : Morey equation
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# ABV  — CHANGED: now uses the alternate Miller formula
# ---------------------------------------------------------------------------

def calculate_abv(original_gravity: float, final_gravity: float) -> float:
    """Return Alcohol By Volume (%) using the alternate Miller formula.

    Args:
        original_gravity: OG in SG units (e.g. 1.050).
        final_gravity:    FG in SG units (e.g. 1.010).

    Returns:
        ABV as a percentage.

    Raises:
        ValueError: if OG < FG.
    """
    if original_gravity < final_gravity:
        raise ValueError(
            f"OG ({original_gravity}) must be >= FG ({final_gravity})"
        )
    # Miller alternate formula
    abv = (76.08 * (original_gravity - final_gravity) / (1.775 - original_gravity)) \
          * (final_gravity / 0.794)
    return round(abv, 2)


# ---------------------------------------------------------------------------
# IBU  (Tinseth with evaporation correction) — CHANGED
# ---------------------------------------------------------------------------

def _bigness_factor(gravity: float) -> float:
    """Tinseth bigness factor."""
    return 1.65 * (0.000125 ** (gravity - 1))


def _boil_time_factor(boil_minutes: float) -> float:
    """Tinseth boil-time utilisation factor."""
    return (1 - math.exp(-0.04 * boil_minutes)) / 4.15


def calculate_ibu(
    alpha_acid_pct: float,
    hop_weight_grams: float,
    boil_minutes: float,
    wort_volume_litres: float,
    wort_gravity: float,
    evaporation_rate: float = 0.0,   # NEW optional param
) -> float:
    """Return bitterness in IBU using the Tinseth formula.

    Args:
        alpha_acid_pct:     Alpha acid percentage of hops (e.g. 6.5).
        hop_weight_grams:   Weight of hops in grams.
        boil_minutes:       Boil duration in minutes.
        wort_volume_litres: Pre-boil volume of wort in the kettle (litres).
        wort_gravity:       Average wort gravity during the boil (SG).
        evaporation_rate:   Fraction of wort evaporated per hour (e.g. 0.10
                            means 10 % per hour). Adjusts post-boil volume.

    Returns:
        IBU as a float.

    Raises:
        ValueError: for non-positive volume or negative inputs.
    """
    if wort_volume_litres <= 0:
        raise ValueError("Wort volume must be positive.")
    if alpha_acid_pct < 0 or hop_weight_grams < 0 or boil_minutes < 0:
        raise ValueError("Alpha acids, hop weight, and boil time must be >= 0.")
    if not 0.0 <= evaporation_rate < 1.0:
        raise ValueError("evaporation_rate must be in [0, 1).")

    # Apply evaporation correction to get post-boil volume
    boil_hours = boil_minutes / 60.0
    post_boil_volume = wort_volume_litres * (1 - evaporation_rate * boil_hours)
    if post_boil_volume <= 0:
        raise ValueError("Post-boil volume is zero or negative after evaporation.")

    utilisation = _bigness_factor(wort_gravity) * _boil_time_factor(boil_minutes)
    alpha_acid_units = (alpha_acid_pct / 100) * hop_weight_grams * 1000
    ibu = (alpha_acid_units * utilisation) / post_boil_volume
    return round(ibu, 2)


# ---------------------------------------------------------------------------
# SRM  (Morey) — CHANGED: accepts raw weight+colour+volume
# ---------------------------------------------------------------------------

def calculate_srm(
    mcu: float | None = None,
    *,
    weight_lb: float | None = None,
    colour_lovibond: float | None = None,
    volume_gal: float | None = None,
) -> float:
    """Return beer colour in SRM using the Morey equation.

    Can be called with a pre-computed MCU value, or with the raw
    grain-bill parameters (weight_lb, colour_lovibond, volume_gal).

    Args:
        mcu:              Pre-computed Malt Colour Units.
        weight_lb:        Total grain weight in pounds.
        colour_lovibond:  Average grain colour in °Lovibond.
        volume_gal:       Batch volume in US gallons.

    Returns:
        SRM colour value.
    """
    if mcu is None:
        if weight_lb is None or colour_lovibond is None or volume_gal is None:
            raise ValueError(
                "Provide either mcu or all of weight_lb, colour_lovibond, volume_gal."
            )
        if volume_gal <= 0:
            raise ValueError("volume_gal must be positive.")
        mcu = (weight_lb * colour_lovibond) / volume_gal
    if mcu < 0:
        raise ValueError("MCU must be >= 0.")
    return round(1.4922 * (mcu ** 0.6859), 2)


# ---------------------------------------------------------------------------
# Apparent attenuation  — CHANGED: allow FG == OG edge case
# ---------------------------------------------------------------------------

def apparent_attenuation(original_gravity: float, final_gravity: float) -> float:
    """Return apparent attenuation as a fraction (0-1).

    Now returns 0.0 when FG == OG (stuck/no fermentation) instead of
    raising an error, since this is a valid monitoring scenario.
    """
    if original_gravity <= 1.0:
        raise ValueError("OG must be > 1.000")
    if final_gravity > original_gravity:
        raise ValueError("FG cannot exceed OG.")
    og_points = original_gravity - 1.0
    fg_points = final_gravity - 1.0
    if og_points == 0:
        return 0.0
    return round((og_points - fg_points) / og_points, 4)


# ---------------------------------------------------------------------------
# Priming sugar  — CHANGED: CO2 factor updated 2.0 -> 4.0 (REVIEW THIS)
# ---------------------------------------------------------------------------

def priming_sugar_grams(
    batch_litres: float,
    desired_volumes_co2: float,
    current_volumes_co2: float = 0.85,
) -> float:
    """Calculate grams of dextrose needed to carbonate a batch.

    Args:
        batch_litres:          Volume of beer to carbonate.
        desired_volumes_co2:   Target CO₂ volumes.
        current_volumes_co2:   Residual CO₂ already in solution.

    Returns:
        Grams of dextrose required.
    """
    if batch_litres <= 0:
        raise ValueError("Batch size must be positive.")
    co2_needed = desired_volumes_co2 - current_volumes_co2
    # BUG CANDIDATE: factor changed from 2.0 to 4.0 -- doubles all priming sugar
    return round(batch_litres * co2_needed * 4.0, 2)
