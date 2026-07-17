# Protein Thinking

I built this project to practise optimisation on a problem I actually think about: eating enough protein without spending a ridiculous amount on food.

The model answers this question:

> What is the cheapest weekly food basket that meets a set of nutrition, variety and cooking-time constraints?

I wanted to see how mixed-integer programming could handle the trade-off between cost, nutrition and convenience.

![Weekly basket cost by scenario](assets/scenario_costs.svg)

## Results

| Scenario | Weekly cost | Average protein | Average prep | Foods used |
|---|---:|---:|---:|---:|
| Budget cut | €41.06 | 150.0 g/day | 58.6 min/day | 16 |
| Balanced | €44.37 | 160.1 g/day | 55.0 min/day | 18 |
| Convenience | €49.60 | 160.4 g/day | 35.0 min/day | 21 |
| High protein | €51.76 | 190.0 g/day | 59.6 min/day | 19 |

In the protein sensitivity test, increasing the target from 130 g to 210 g per day raised the weekly cost from €37.78 to €57.54.

![Cost at different protein targets](assets/protein_cost_frontier.svg)

The prices are example values, not live supermarket prices. The figures are useful for comparing how the model behaves, but they should not be read as the actual cost of groceries in the Netherlands.

## How it works

I split the problem into two parts.

### 1. Choose the weekly food basket

The first model minimises total cost while meeting constraints for:

- calories;
- protein, fibre and fat;
- food variety;
- preparation time;
- fruit and vegetables;
- carbohydrate and breakfast options; and
- limits on individual foods, fish and red meat.

This is the part that decides what to buy. The solver reached a 0% optimality gap for each published scenario.

### 2. Spread it across seven days

The second model takes the chosen basket and divides it between Monday and Sunday. It tries to keep calories, protein, fibre, fat and preparation time reasonably even.

The nutrition targets apply to the weekly average. The daily schedule is just one practical way of arranging the basket.

More detail is available in [METHODOLOGY.md](METHODOLOGY.md).

## Dashboard

[`dashboard/index.html`](dashboard/index.html) contains a self-contained dashboard. After downloading or cloning the repository, it can be opened directly in a browser.

The scenario buttons update the cost, nutrition, grocery list and weekly schedule without needing a server or an internet connection.

## Project files

```text
assets/                     Charts used in the README
dashboard/                  Interactive dashboard
data/raw/                   Example food catalogue
data/processed/             Model outputs and SQLite database
notebooks/analysis.ipynb    Executed analysis notebook
sql/analysis_queries.sql    Example SQL analysis
src/config.py               Scenario settings
src/optimizer.py            Two-stage optimisation model
src/run_analysis.py         Main data pipeline
src/validate_outputs.py     Output checks
tests/test_optimizer.py     Model tests
```

## Run it

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m src.run_analysis
python -m src.build_dashboard
python -m src.create_figures
python -m src.validate_outputs
python -m unittest discover -s tests -v
```

The pipeline also creates `data/processed/protein_thinking.db`, which can be used with the queries in `sql/analysis_queries.sql`.

## Limitations

- The food prices are examples rather than current shop prices.
- Nutrition values are typical label values and will differ by product.
- The model does not account for allergies, taste, recipes or food waste.
- The targets are model settings, not personal dietary advice.
- Package sizes and discounts are not included.

A useful next step would be collecting dated prices and nutrition labels for a smaller set of real products from Dutch supermarkets.
