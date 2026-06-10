# 🍺 Brewery Platform

Craft brewery operations platform — tools, calculators, and utilities for batch management, costing, and recipe analysis.

## Modules

| Module | Description |
|--------|-------------|
| `brewery/calculations.py` | Core brewing math: ABV, IBU (Tinseth), SRM (Morey), gravity correction |
| `brewery/recipe.py` | Recipe dataclass with derived metrics |

## Quick Start

```python
from brewery.recipe import Recipe, HopAddition, GrainBill

recipe = Recipe(
    name="Cascade Pale Ale",
    batch_size_gallons=5.0,
    original_gravity=1.055,
    final_gravity=1.012,
    hops=[HopAddition("Cascade", 5.5, 1.5, 60)],
    grains=[GrainBill("2-Row Pale", 10.0, 2.0)],
)
print(recipe.summary())
```

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
