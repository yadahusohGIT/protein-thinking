"""Regression tests for the optimisation model and generated outputs."""

from __future__ import annotations

import unittest
from pathlib import Path

from src.config import SCENARIOS
from src.optimizer import DAYS, load_catalog, optimise_meal_plan


ROOT = Path(__file__).resolve().parents[1]


class OptimizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_catalog(ROOT / "data" / "raw" / "food_catalog.csv")
        cls.scenario = SCENARIOS["balanced"]
        cls.result = optimise_meal_plan(cls.catalog, cls.scenario)

    def test_every_day_is_present(self) -> None:
        self.assertEqual(set(self.result["daily"]["day"]), set(DAYS))

    def test_weekly_average_nutrient_constraints_hold(self) -> None:
        daily = self.result["daily"]
        self.assertTrue(self.scenario.calorie_min <= daily["kcal"].mean() <= self.scenario.calorie_max)
        self.assertGreaterEqual(daily["protein_g"].mean(), self.scenario.protein_min_g)
        self.assertGreaterEqual(daily["fibre_g"].mean(), self.scenario.fibre_min_g)
        self.assertTrue(self.scenario.fat_min_g <= daily["fat_g"].mean() <= self.scenario.fat_max_g)
        self.assertLessEqual(daily["prep_minutes"].mean(), self.scenario.max_prep_minutes)

    def test_variety_and_frequency_constraints_hold(self) -> None:
        plan = self.result["plan"]
        self.assertGreaterEqual(plan["food_id"].nunique(), self.scenario.min_weekly_foods)
        self.assertTrue((self.result["daily"]["distinct_foods"] >= self.scenario.min_daily_items).all())
        food_totals = plan.groupby("food_id")["servings"].sum()
        weekly_caps = self.catalog.set_index("food_id")["max_servings_week"]
        for food_id, servings in food_totals.items():
            self.assertLessEqual(servings, weekly_caps.loc[food_id])

    def test_cost_reconciles(self) -> None:
        plan_cost = round(float(self.result["plan"]["cost_eur"].sum()), 2)
        self.assertEqual(plan_cost, self.result["summary"]["weekly_cost_eur"])


if __name__ == "__main__":
    unittest.main()
