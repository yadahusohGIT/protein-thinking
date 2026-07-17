# Methodology

## Why I used two models

I first tried treating every food on every day as one large cost-minimisation problem. It worked, but there were many nearly identical solutions because the days could be swapped without changing the shopping cost.

So I separated the purchasing decision from the daily schedule:

1. find the cheapest weekly basket;
2. keep that basket fixed and spread it across seven days.

This makes the result easier to explain and lets the first model prove the minimum shopping cost without wasting time comparing equivalent schedules.

## Input data

`data/raw/food_catalog.csv` contains 29 foods. Each row includes:

- price and serving size;
- calories, protein, carbohydrates, fat and fibre;
- estimated preparation time;
- daily and weekly serving limits; and
- simple labels such as breakfast food, dinner protein, produce or carbohydrate source.

The prices are examples based on ordinary grocery items. They are not scraped or updated automatically. Nutrition values are typical label values.

## Stage 1: weekly basket

For every food `i`, the model uses:

- `x_i`: number of servings bought during the week;
- `y_i`: whether the food appears in the basket.

The main objective is:

```text
minimise sum(price_i × x_i)
```

The convenience scenario also gives a small penalty to preparation time. The reported monetary cost still uses food prices only.

### Main constraints

Weekly nutrition totals must satisfy seven times the daily-average settings:

```text
7 × minimum calories <= weekly calories <= 7 × maximum calories
weekly protein >= 7 × protein target
weekly fibre >= 7 × fibre target
7 × minimum fat <= weekly fat <= 7 × maximum fat
weekly preparation <= 7 × preparation limit
```

I also added practical constraints:

- at least 13 or 14 different foods;
- seven dinner-protein servings from at least four different foods;
- at least 14 produce servings;
- at least 14 carbohydrate servings;
- enough breakfast options for the week;
- no more than three fish servings;
- no more than two red-meat servings; and
- limits for every individual food.

All four published basket solutions reached a reported MIP gap of 0%.

## Stage 2: daily schedule

The weekly quantities from Stage 1 cannot change in Stage 2:

```text
sum(daily servings of food i) = weekly servings of food i
```

The scheduling model then tries to reduce the difference between each day's calories, protein, fibre, fat and preparation time. Each day also needs a dinner protein, breakfast option, produce and carbohydrate source.

The scheduling objective is secondary. It is allowed to stop within a 5% solver gap because it does not change the minimum weekly basket cost.

## Scenario settings

| Scenario | Calories | Protein | Fibre | Fat | Prep limit |
|---|---:|---:|---:|---:|---:|
| Balanced | 2,500 ± 100 | 160 g | 30 g | 60–100 g | 55 min |
| Budget cut | 2,300 ± 100 | 150 g | 28 g | 55–90 g | 60 min |
| High protein | 2,600 ± 100 | 190 g | 30 g | 60–105 g | 60 min |
| Convenience | 2,400 ± 100 | 160 g | 28 g | 55–95 g | 35 min |

These are settings used to test the model, not recommendations for a person's diet.

## Protein sensitivity test

I reran the balanced model nine times with protein targets from 130 g to 210 g. Everything else stayed the same. This shows how the minimum cost changes when only the protein constraint becomes stricter.

## Checks

The validation script and tests check that:

- required input columns exist;
- food IDs are unique;
- prices and nutrition values are valid;
- weekly nutrition and preparation constraints hold;
- food-level costs match the reported totals;
- all seven days are present;
- the basket solutions are optimal; and
- the sensitivity results stay ordered as the protein target rises.

## What the model leaves out

It does not include live prices, discounts, package sizes, recipes, allergies, taste or food waste. Those would all matter before using it as an actual shopping tool.
