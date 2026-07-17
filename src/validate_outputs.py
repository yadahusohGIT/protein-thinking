"""Validate generated analytical outputs before portfolio publication."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import SCENARIOS


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def validate() -> list[str]:
    plan = pd.read_csv(PROCESSED / "meal_plan.csv")
    daily = pd.read_csv(PROCESSED / "daily_summary.csv")
    summary = pd.read_csv(PROCESSED / "scenario_summary.csv").set_index("scenario")
    frontier = pd.read_csv(PROCESSED / "protein_frontier.csv")

    checks: list[tuple[bool, str]] = []
    checks.append((set(summary.index) == set(SCENARIOS), "all four scenarios are present"))
    checks.append((not plan.duplicated(["scenario", "day", "food_id"]).any(), "plan grain is unique"))
    checks.append(((daily.groupby("scenario")["day"].nunique() == 7).all(), "every scenario has seven days"))
    checks.append(((summary["solver_mip_gap"].fillna(0) <= 0.001).all(), "weekly cost solutions are optimal"))
    checks.append((frontier["protein_floor_g"].is_monotonic_increasing, "protein frontier is ordered"))
    checks.append((frontier["weekly_cost_eur"].is_monotonic_increasing, "frontier cost is monotonic"))
    for key, scenario in SCENARIOS.items():
        row = summary.loc[key]
        checks.extend(
            [
                (scenario.calorie_min <= row.average_kcal <= scenario.calorie_max, f"{key}: average calories satisfy bounds"),
                (row.average_protein_g >= scenario.protein_min_g, f"{key}: average protein satisfies floor"),
                (row.average_fibre_g >= scenario.fibre_min_g, f"{key}: average fibre satisfies floor"),
                (scenario.fat_min_g <= row.average_fat_g <= scenario.fat_max_g, f"{key}: average fat satisfies bounds"),
                (row.average_prep_minutes <= scenario.max_prep_minutes, f"{key}: average preparation satisfies cap"),
            ]
        )

    failures = [label for passed, label in checks if not passed]
    if failures:
        raise AssertionError("Validation failed:\n- " + "\n- ".join(failures))
    return [label for _, label in checks]


if __name__ == "__main__":
    passed = validate()
    print(f"{len(passed)} validation checks passed")
    for item in passed:
        print(f"- {item}")

