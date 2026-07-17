"""Mixed-integer meal-plan optimisation for Protein Thinking."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

from src.config import Scenario


DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
NUTRIENTS = ("kcal", "protein_g", "carbs_g", "fat_g", "fibre_g")
FLAG_COLUMNS = (
    "breakfast_anchor",
    "dinner_protein",
    "carb_base",
    "produce",
    "supplement",
    "fish",
    "red_meat",
    "vegetarian",
)


def load_catalog(path: str | Path) -> pd.DataFrame:
    """Load and validate the versioned illustrative food catalogue."""

    catalog = pd.read_csv(path)
    required = {
        "food_id",
        "food_name",
        "category",
        "meal_slot",
        "serving_description",
        "serving_g",
        "price_eur",
        "prep_minutes",
        "max_servings_day",
        "max_servings_week",
        *NUTRIENTS,
        *FLAG_COLUMNS,
    }
    missing = sorted(required.difference(catalog.columns))
    if missing:
        raise ValueError(f"Food catalogue is missing columns: {missing}")
    if catalog["food_id"].duplicated().any():
        raise ValueError("food_id values must be unique")
    numeric_columns = [
        "serving_g",
        "price_eur",
        "prep_minutes",
        "max_servings_day",
        "max_servings_week",
        *NUTRIENTS,
        *FLAG_COLUMNS,
    ]
    if catalog[numeric_columns].isna().any().any():
        raise ValueError("Numeric food catalogue values cannot be missing")
    if (catalog[["serving_g", "price_eur", "kcal", "protein_g"]] < 0).any().any():
        raise ValueError("Serving size, price and headline nutrition values cannot be negative")
    return catalog.reset_index(drop=True)


def optimise_meal_plan(catalog: pd.DataFrame, scenario: Scenario) -> dict[str, pd.DataFrame | dict]:
    """Solve a two-stage weekly basket and daily scheduling model.

    Stage 1 finds the exact lowest-cost weekly basket. Stage 2 keeps that basket
    fixed and distributes servings across seven days to reduce nutritional and
    preparation-time variation. Nutritional constraints therefore apply to the
    weekly average; daily rows are an illustrative schedule of the same basket.
    """

    n_days = len(DAYS)
    n_foods = len(catalog)

    # Stage 1: weekly cost minimisation.
    n_stage_one_vars = n_foods * 2
    weekly_objective = np.zeros(n_stage_one_vars, dtype=float)
    weekly_lower = np.zeros(n_stage_one_vars, dtype=float)
    weekly_upper = np.ones(n_stage_one_vars, dtype=float)
    for food in range(n_foods):
        weekly_objective[food] = (
            float(catalog.at[food, "price_eur"])
            + scenario.prep_cost_weight * float(catalog.at[food, "prep_minutes"])
            + 1e-6 * food
        )
        weekly_upper[food] = float(catalog.at[food, "max_servings_week"])

    stage_one_rows: list[np.ndarray] = []
    stage_one_lower: list[float] = []
    stage_one_upper: list[float] = []

    def add_weekly(coefficients: dict[int, float], lb: float = -np.inf, ub: float = np.inf) -> None:
        row = np.zeros(n_stage_one_vars, dtype=float)
        for index, value in coefficients.items():
            row[index] = value
        stage_one_rows.append(row)
        stage_one_lower.append(lb)
        stage_one_upper.append(ub)

    for food in range(n_foods):
        selected = n_foods + food
        cap = float(catalog.at[food, "max_servings_week"])
        add_weekly({food: 1, selected: -cap}, ub=0)
        add_weekly({food: 1, selected: -1}, lb=0)

    for nutrient, lb, ub in (
        ("kcal", 7 * scenario.calorie_min, 7 * scenario.calorie_max),
        ("protein_g", 7 * scenario.protein_min_g, np.inf),
        ("fibre_g", 7 * scenario.fibre_min_g, np.inf),
        ("fat_g", 7 * scenario.fat_min_g, 7 * scenario.fat_max_g),
    ):
        add_weekly(
            {food: float(catalog.at[food, nutrient]) for food in range(n_foods)},
            lb=lb,
            ub=ub,
        )
    add_weekly(
        {food: float(catalog.at[food, "prep_minutes"]) for food in range(n_foods)},
        ub=7 * scenario.max_prep_minutes,
    )
    add_weekly(
        {n_foods + food: 1 for food in range(n_foods)},
        lb=scenario.min_weekly_foods,
    )
    add_weekly(
        {
            n_foods + food: 1
            for food in range(n_foods)
            if int(catalog.at[food, "dinner_protein"]) == 1
        },
        lb=scenario.min_dinner_proteins,
    )
    for flag, lb, ub in (
        ("breakfast_anchor", 7, np.inf),
        ("dinner_protein", 7, 7),
        ("carb_base", 14, np.inf),
        ("produce", 14, np.inf),
        ("supplement", -np.inf, 7),
        ("fish", -np.inf, 3),
        ("red_meat", -np.inf, 2),
    ):
        add_weekly(
            {
                food: 1
                for food in range(n_foods)
                if int(catalog.at[food, flag]) == 1
            },
            lb=lb,
            ub=ub,
        )

    weekly_result = milp(
        c=weekly_objective,
        integrality=np.ones(n_stage_one_vars, dtype=int),
        bounds=Bounds(weekly_lower, weekly_upper),
        constraints=LinearConstraint(
            np.vstack(stage_one_rows),
            np.array(stage_one_lower),
            np.array(stage_one_upper),
        ),
        options={"time_limit": 30, "mip_rel_gap": 0.0},
    )
    if weekly_result.x is None:
        raise RuntimeError(f"Scenario {scenario.key!r} did not solve: {weekly_result.message}")
    weekly_servings = np.rint(weekly_result.x[:n_foods]).astype(int)

    # Stage 2: distribute the fixed basket while minimising daily variation.
    balance_metrics = {
        "kcal": scenario.calorie_target,
        "protein_g": scenario.protein_min_g,
        "fibre_g": scenario.fibre_min_g,
        "fat_g": (scenario.fat_min_g + scenario.fat_max_g) / 2,
        "prep_minutes": scenario.max_prep_minutes * 0.75,
    }
    n_x = n_days * n_foods
    n_deviation = n_days * len(balance_metrics) * 2
    n_stage_two_vars = n_x + n_deviation

    def daily_x(day: int, food: int) -> int:
        return day * n_foods + food

    metric_names = list(balance_metrics)

    def positive_dev(day: int, metric: int) -> int:
        return n_x + (day * len(metric_names) + metric) * 2

    def negative_dev(day: int, metric: int) -> int:
        return positive_dev(day, metric) + 1

    schedule_objective = np.zeros(n_stage_two_vars, dtype=float)
    schedule_lower = np.zeros(n_stage_two_vars, dtype=float)
    schedule_upper = np.full(n_stage_two_vars, np.inf, dtype=float)
    schedule_integrality = np.zeros(n_stage_two_vars, dtype=int)
    for day in range(n_days):
        for food in range(n_foods):
            schedule_upper[daily_x(day, food)] = min(
                float(catalog.at[food, "max_servings_day"]),
                float(weekly_servings[food]),
            )
            schedule_integrality[daily_x(day, food)] = 1
        for metric, name in enumerate(metric_names):
            scale = max(float(balance_metrics[name]), 1.0)
            schedule_objective[positive_dev(day, metric)] = 1 / scale
            schedule_objective[negative_dev(day, metric)] = 1 / scale

    schedule_rows: list[np.ndarray] = []
    schedule_lbs: list[float] = []
    schedule_ubs: list[float] = []

    def add_schedule(coefficients: dict[int, float], lb: float = -np.inf, ub: float = np.inf) -> None:
        row = np.zeros(n_stage_two_vars, dtype=float)
        for index, value in coefficients.items():
            row[index] = value
        schedule_rows.append(row)
        schedule_lbs.append(lb)
        schedule_ubs.append(ub)

    for food in range(n_foods):
        add_schedule(
            {daily_x(day, food): 1 for day in range(n_days)},
            lb=float(weekly_servings[food]),
            ub=float(weekly_servings[food]),
        )

    for day in range(n_days):
        for flag, lb, ub in (
            ("breakfast_anchor", 1, np.inf),
            ("dinner_protein", 1, 1),
            ("carb_base", 2, np.inf),
            ("produce", 2, np.inf),
            ("supplement", -np.inf, 1),
        ):
            add_schedule(
                {
                    daily_x(day, food): 1
                    for food in range(n_foods)
                    if int(catalog.at[food, flag]) == 1
                },
                lb=lb,
                ub=ub,
            )
        add_schedule(
            {daily_x(day, food): 1 for food in range(n_foods)},
            lb=scenario.min_daily_items,
            ub=scenario.max_daily_items + 3,
        )
        # Broad guardrails prevent an even weekly basket from producing an
        # implausibly extreme individual day.
        for nutrient, lb, ub in (
            ("kcal", scenario.calorie_target - 300, scenario.calorie_target + 300),
            ("protein_g", max(0, scenario.protein_min_g - 30), np.inf),
            ("fibre_g", max(0, scenario.fibre_min_g - 12), np.inf),
            ("fat_g", max(0, scenario.fat_min_g - 25), scenario.fat_max_g + 30),
            ("prep_minutes", -np.inf, scenario.max_prep_minutes + 20),
        ):
            add_schedule(
                {daily_x(day, food): float(catalog.at[food, nutrient]) for food in range(n_foods)},
                lb=lb,
                ub=ub,
            )
        for metric, name in enumerate(metric_names):
            coefficients = {
                daily_x(day, food): float(catalog.at[food, name]) for food in range(n_foods)
            }
            coefficients[positive_dev(day, metric)] = -1
            coefficients[negative_dev(day, metric)] = 1
            target = float(balance_metrics[name])
            add_schedule(coefficients, lb=target, ub=target)

    schedule_result = milp(
        c=schedule_objective,
        integrality=schedule_integrality,
        bounds=Bounds(schedule_lower, schedule_upper),
        constraints=LinearConstraint(
            np.vstack(schedule_rows), np.array(schedule_lbs), np.array(schedule_ubs)
        ),
        options={"time_limit": 6, "mip_rel_gap": 0.05},
    )
    if schedule_result.x is None:
        raise RuntimeError(f"Scenario {scenario.key!r} could not be scheduled: {schedule_result.message}")
    servings = np.rint(schedule_result.x[:n_x]).astype(int).reshape(n_days, n_foods)
    plan_rows: list[dict] = []
    for day_index, day_name in enumerate(DAYS):
        for food in range(n_foods):
            quantity = int(servings[day_index, food])
            if quantity == 0:
                continue
            row = {
                "scenario": scenario.key,
                "scenario_label": scenario.label,
                "day_number": day_index + 1,
                "day": day_name,
                "food_id": catalog.at[food, "food_id"],
                "food_name": catalog.at[food, "food_name"],
                "category": catalog.at[food, "category"],
                "meal_slot": catalog.at[food, "meal_slot"],
                "serving_description": catalog.at[food, "serving_description"],
                "servings": quantity,
                "serving_g": float(catalog.at[food, "serving_g"]) * quantity,
                "cost_eur": float(catalog.at[food, "price_eur"]) * quantity,
                "prep_minutes": float(catalog.at[food, "prep_minutes"]) * quantity,
            }
            for nutrient in NUTRIENTS:
                row[nutrient] = float(catalog.at[food, nutrient]) * quantity
            plan_rows.append(row)

    plan = pd.DataFrame(plan_rows)
    daily = (
        plan.groupby(["scenario", "scenario_label", "day_number", "day"], as_index=False)
        .agg(
            cost_eur=("cost_eur", "sum"),
            kcal=("kcal", "sum"),
            protein_g=("protein_g", "sum"),
            carbs_g=("carbs_g", "sum"),
            fat_g=("fat_g", "sum"),
            fibre_g=("fibre_g", "sum"),
            prep_minutes=("prep_minutes", "sum"),
            distinct_foods=("food_id", "nunique"),
        )
        .sort_values("day_number")
    )
    summary = {
        "scenario": scenario.key,
        "scenario_label": scenario.label,
        "description": scenario.description,
        "weekly_cost_eur": round(float(daily["cost_eur"].sum()), 2),
        "average_daily_cost_eur": round(float(daily["cost_eur"].mean()), 2),
        "average_kcal": round(float(daily["kcal"].mean()), 1),
        "average_protein_g": round(float(daily["protein_g"].mean()), 1),
        "average_fibre_g": round(float(daily["fibre_g"].mean()), 1),
        "average_fat_g": round(float(daily["fat_g"].mean()), 1),
        "average_prep_minutes": round(float(daily["prep_minutes"].mean()), 1),
        "unique_foods": int(plan["food_id"].nunique()),
        "solver_objective": float(weekly_result.fun),
        "solver_status": weekly_result.message,
        "solver_mip_gap": float(getattr(weekly_result, "mip_gap", np.nan)),
        "schedule_status": schedule_result.message,
        "schedule_mip_gap": float(getattr(schedule_result, "mip_gap", np.nan)),
        **{f"target_{key}": value for key, value in asdict(scenario).items() if isinstance(value, (int, float))},
    }
    return {"plan": plan, "daily": daily, "summary": summary}
