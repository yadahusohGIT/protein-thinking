# LinkedIn post draft

I’ve finished my second Business Analytics portfolio project: **Protein Thinking — a cost-constrained student meal-planning optimiser**.

After my Maastricht neighbourhood analysis, I wanted to build something that demonstrated a different analytical skill: making a decision under competing constraints.

I created a two-stage mixed-integer model in Python. The first stage finds the minimum-cost weekly grocery basket subject to nutrition, variety, preparation-time and food-frequency constraints. The second stage arranges that fixed basket across seven days.

Using a clearly labelled illustrative Dutch retail catalogue, the balanced scenario produced:

- €44.37 illustrative weekly cost
- 160.1 g average protein per day
- 18 distinct foods
- a proven 0% solver gap for the basket decision

The sensitivity analysis also showed that raising the protein floor from 130 g to 210 g increased the modelled weekly cost by €19.76.

The project includes Python, MILP optimisation, SQL/SQLite, automated validation, an executed Jupyter notebook and an interactive dashboard.

Important caveat: the prices are reproducible assumptions rather than a live supermarket feed, so the findings demonstrate the decision model—not current Dutch grocery prices.

Repository: https://github.com/yadahusohGIT/protein-thinking

#BusinessAnalytics #Python #OperationsResearch #SQL #DataAnalytics #PortfolioProject

