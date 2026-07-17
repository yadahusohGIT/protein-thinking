"""Run every portfolio scenario and materialise reproducible outputs."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import SCENARIOS, protein_frontier_scenarios
from src.optimizer import load_catalog, optimise_meal_plan


ROOT = Path(__file__).resolve().parents[1]
RAW_CATALOG = ROOT / "data" / "raw" / "food_catalog.csv"
PROCESSED = ROOT / "data" / "processed"


def run() -> dict[str, pd.DataFrame]:
    """Solve the main scenarios, sensitivity frontier and SQLite analytical layer."""

    PROCESSED.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog(RAW_CATALOG)

    solved = [optimise_meal_plan(catalog, scenario) for scenario in SCENARIOS.values()]
    plan = pd.concat([item["plan"] for item in solved], ignore_index=True)
    daily = pd.concat([item["daily"] for item in solved], ignore_index=True)
    summary = pd.DataFrame([item["summary"] for item in solved])

    frontier_rows = []
    for scenario in protein_frontier_scenarios():
        output = optimise_meal_plan(catalog, scenario)
        frontier_rows.append(
            {
                "protein_floor_g": scenario.protein_min_g,
                "weekly_cost_eur": output["summary"]["weekly_cost_eur"],
                "average_protein_g": output["summary"]["average_protein_g"],
                "unique_foods": output["summary"]["unique_foods"],
            }
        )
    frontier = pd.DataFrame(frontier_rows)
    frontier["incremental_cost_vs_130_eur"] = (
        frontier["weekly_cost_eur"] - frontier["weekly_cost_eur"].iloc[0]
    ).round(2)

    grocery = (
        plan.groupby(["scenario", "scenario_label", "food_id", "food_name", "category"], as_index=False)
        .agg(servings=("servings", "sum"), weekly_cost_eur=("cost_eur", "sum"))
        .sort_values(["scenario", "weekly_cost_eur"], ascending=[True, False])
    )
    grocery["weekly_cost_eur"] = grocery["weekly_cost_eur"].round(2)

    outputs = {
        "meal_plan": plan,
        "daily_summary": daily,
        "scenario_summary": summary,
        "protein_frontier": frontier,
        "grocery_list": grocery,
    }
    for name, frame in outputs.items():
        frame.to_csv(PROCESSED / f"{name}.csv", index=False)

    database_path = PROCESSED / "protein_thinking.db"
    if database_path.exists():
        database_path.unlink()
    with sqlite3.connect(database_path) as connection:
        catalog.to_sql("food_catalog", connection, index=False)
        for name, frame in outputs.items():
            frame.to_sql(name, connection, index=False)

    return outputs


if __name__ == "__main__":
    generated = run()
    print(
        generated["scenario_summary"][["scenario_label", "weekly_cost_eur", "average_protein_g"]]
        .to_string(index=False)
    )

