# Methodology

## 1. Decision and unit of analysis

The decision is which integer number of food servings to purchase for a seven-day period. The unit of analysis in Stage 1 is a **food serving per week**. Stage 2 changes the unit to a **food serving per day** while keeping the Stage 1 weekly totals fixed.

This separation is intentional. Purchasing decisions are normally made at basket level, while practical scheduling is a different objective. Combining both stages into one large daily-cost model creates many interchangeable day permutations without changing the purchasing recommendation.

## 2. Inputs

Each food has:

- an identifier, name, category and suggested meal slot;
- serving size and illustrative price;
- energy, protein, carbohydrate, fat and fibre per serving;
- active preparation minutes;
- daily and weekly serving caps; and
- binary role flags such as breakfast anchor, dinner protein, carbohydrate base, produce, supplement, fish and red meat.

The catalogue contains 29 foods. It is a reproducible portfolio input, not a live market dataset.

## 3. Stage 1: weekly basket optimisation

### Decision variables

For food *i*:

- `x_i` = integer servings purchased during the week;
- `y_i` = 1 when the food appears in the basket, otherwise 0.

### Objective

The standard scenarios minimise:

```text
sum_i(price_i × x_i)
```

The convenience scenario adds a small preparation-time penalty to prefer less active cooking when two baskets have similar monetary cost. Reported basket cost always uses actual illustrative prices only.

### Nutrition constraints

The weekly totals must fall inside seven times the daily-average bounds:

```text
7 × calorie_min <= sum_i(kcal_i × x_i) <= 7 × calorie_max
sum_i(protein_i × x_i) >= 7 × protein_min
sum_i(fibre_i × x_i) >= 7 × fibre_min
7 × fat_min <= sum_i(fat_i × x_i) <= 7 × fat_max
sum_i(prep_i × x_i) <= 7 × prep_max
```

### Practical constraints

- at least 13 or 14 distinct foods, depending on scenario;
- at least seven breakfast-anchor servings;
- exactly seven dinner-protein servings;
- at least four distinct dinner-protein foods;
- at least 14 carbohydrate-base servings;
- at least 14 produce servings;
- no more than seven supplement servings;
- no more than three fish servings;
- no more than two red-meat servings; and
- food-specific weekly serving caps.

The linking rules `x_i <= weekly_cap_i × y_i` and `x_i >= y_i` make the variety counts valid.

## 4. Stage 2: daily allocation

Stage 2 fixes each weekly serving total from Stage 1:

```text
sum_d(x_di) = optimised weekly servings_i
```

The scheduler minimises scaled absolute deviation from scenario reference values for:

- calories;
- protein;
- fibre;
- fat; and
- active preparation time.

It also requires each day to contain one dinner-protein serving, at least one breakfast anchor, at least two carbohydrate-base servings, at least two produce servings and no more than one supplement serving.

Broad day-level guardrails prevent extreme allocations. The portfolio's nutritional claims remain weekly-average claims because Stage 1 owns the hard nutrition decision.

## 5. Scenarios

| Scenario | Calorie target | Protein floor | Fibre floor | Fat range | Prep cap | Minimum foods |
|---|---:|---:|---:|---:|---:|---:|
| Balanced | 2,500 ± 100 | 160 g | 30 g | 60–100 g | 55 min | 14 |
| Budget cut | 2,300 ± 100 | 150 g | 28 g | 55–90 g | 60 min | 13 |
| High protein | 2,600 ± 100 | 190 g | 30 g | 60–105 g | 60 min | 14 |
| Convenience | 2,400 ± 100 | 160 g | 28 g | 55–95 g | 35 min | 13 |

These values are scenario parameters for demonstrating the optimisation model. They are not personalised nutritional recommendations.

## 6. Protein sensitivity

The sensitivity analysis reruns the balanced weekly basket model at protein floors from 130 g to 210 g in 10 g increments. All other balanced constraints remain unchanged. Because the same catalogue and model structure are used, changes in the minimum objective isolate the cost effect of tightening the protein constraint within this model.

## 7. Solver and reproducibility

The model uses `scipy.optimize.milp`, which calls the HiGHS mixed-integer solver.

- Stage 1 requests a zero relative MIP gap and reaches 0% for all published scenarios.
- Stage 2 permits a 5% scheduling-objective gap because schedule balance is secondary to the proven basket-cost result.
- A deterministic tie-break term is several orders of magnitude smaller than a cent and prevents arbitrary equal-cost choices from changing between runs.

## 8. Validation

The project checks:

- input columns, uniqueness, missing values and non-negative values;
- weekly nutrition, variety, frequency and preparation constraints;
- reconciliation between food-level and scenario-level costs;
- seven-day coverage and output grain;
- solver optimality gaps for the purchasing decision;
- monotonic ordering of the protein-cost frontier;
- dashboard interaction state and JavaScript errors; and
- notebook execution counts and error outputs.

## 9. Interpretation limits

The model answers a conditional question: **given this catalogue and these constraints, what basket has the lowest objective value?**

It does not establish:

- current prices at a specific supermarket;
- product availability or promotions;
- nutritional suitability for an individual;
- taste, allergies, cultural preferences or food waste;
- recipe compatibility; or
- uncertainty in nutrition labels and prices.

Those limits should travel with every published finding.

