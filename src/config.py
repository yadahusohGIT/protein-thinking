"""Settings for the four meal-planning scenarios."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Scenario:
    """A complete set of daily and weekly planning constraints."""

    key: str
    label: str
    description: str
    calorie_target: float
    calorie_tolerance: float
    protein_min_g: float
    fibre_min_g: float
    fat_min_g: float
    fat_max_g: float
    max_prep_minutes: float
    min_daily_items: int = 7
    max_daily_items: int = 10
    min_weekly_foods: int = 14
    min_dinner_proteins: int = 4
    prep_cost_weight: float = 0.0

    @property
    def calorie_min(self) -> float:
        return self.calorie_target - self.calorie_tolerance

    @property
    def calorie_max(self) -> float:
        return self.calorie_target + self.calorie_tolerance


SCENARIOS: dict[str, Scenario] = {
    "balanced": Scenario(
        key="balanced",
        label="Balanced",
        description="A practical baseline balancing cost, nutrition, variety and preparation time.",
        calorie_target=2_500,
        calorie_tolerance=100,
        protein_min_g=160,
        fibre_min_g=30,
        fat_min_g=60,
        fat_max_g=100,
        max_prep_minutes=55,
    ),
    "budget": Scenario(
        key="budget",
        label="Budget cut",
        description="A lower-calorie, cost-focused plan that retains a high protein floor.",
        calorie_target=2_300,
        calorie_tolerance=100,
        protein_min_g=150,
        fibre_min_g=28,
        fat_min_g=55,
        fat_max_g=90,
        max_prep_minutes=60,
        min_weekly_foods=13,
    ),
    "high_protein": Scenario(
        key="high_protein",
        label="High protein",
        description="Tests the weekly cost of raising the protein constraint to 190 grams per day.",
        calorie_target=2_600,
        calorie_tolerance=100,
        protein_min_g=190,
        fibre_min_g=30,
        fat_min_g=60,
        fat_max_g=105,
        max_prep_minutes=60,
    ),
    "convenience": Scenario(
        key="convenience",
        label="Convenience",
        description="Caps total active preparation at 35 minutes per day and lightly penalises prep time.",
        calorie_target=2_400,
        calorie_tolerance=100,
        protein_min_g=160,
        fibre_min_g=28,
        fat_min_g=55,
        fat_max_g=95,
        max_prep_minutes=35,
        min_weekly_foods=13,
        prep_cost_weight=0.012,
    ),
}


def protein_frontier_scenarios() -> list[Scenario]:
    """Return balanced scenarios with progressively tighter protein floors."""

    baseline = SCENARIOS["balanced"]
    return [
        replace(
            baseline,
            key=f"protein_{protein}",
            label=f"{protein} g",
            description="Protein-cost sensitivity scenario.",
            protein_min_g=float(protein),
        )
        for protein in range(130, 211, 10)
    ]
