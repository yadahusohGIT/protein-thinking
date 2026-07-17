-- Protein Thinking analytical questions
-- Run against data/processed/protein_thinking.db after `python -m src.run_analysis`.

-- 1. Which scenario has the lowest weekly cost and what trade-offs does it make?
SELECT
    scenario_label,
    ROUND(weekly_cost_eur, 2) AS weekly_cost_eur,
    ROUND(average_protein_g, 1) AS average_protein_g,
    ROUND(average_prep_minutes, 1) AS average_prep_minutes,
    unique_foods
FROM scenario_summary
ORDER BY weekly_cost_eur;

-- 2. Which foods account for the largest share of each scenario's basket cost?
WITH ranked_foods AS (
    SELECT
        scenario_label,
        food_name,
        category,
        weekly_cost_eur,
        ROW_NUMBER() OVER (
            PARTITION BY scenario
            ORDER BY weekly_cost_eur DESC, food_name
        ) AS cost_rank
    FROM grocery_list
)
SELECT scenario_label, food_name, category, weekly_cost_eur
FROM ranked_foods
WHERE cost_rank <= 5
ORDER BY scenario_label, cost_rank;

-- 3. How much does each additional protein threshold add to weekly cost?
SELECT
    protein_floor_g,
    weekly_cost_eur,
    ROUND(
        weekly_cost_eur - LAG(weekly_cost_eur) OVER (ORDER BY protein_floor_g),
        2
    ) AS incremental_cost_vs_previous_step_eur
FROM protein_frontier
ORDER BY protein_floor_g;

-- 4. How evenly does the scheduler distribute cost and protein across the week?
SELECT
    scenario_label,
    MIN(cost_eur) AS minimum_daily_cost_eur,
    MAX(cost_eur) AS maximum_daily_cost_eur,
    ROUND(MAX(cost_eur) - MIN(cost_eur), 2) AS daily_cost_range_eur,
    ROUND(MIN(protein_g), 1) AS minimum_daily_protein_g,
    ROUND(MAX(protein_g), 1) AS maximum_daily_protein_g
FROM daily_summary
GROUP BY scenario, scenario_label
ORDER BY scenario_label;

-- 5. What share of balanced-plan spend belongs to each food category?
SELECT
    category,
    ROUND(SUM(cost_eur), 2) AS weekly_cost_eur,
    ROUND(
        100.0 * SUM(cost_eur) / SUM(SUM(cost_eur)) OVER (),
        1
    ) AS cost_share_pct
FROM meal_plan
WHERE scenario = 'balanced'
GROUP BY category
ORDER BY weekly_cost_eur DESC;

