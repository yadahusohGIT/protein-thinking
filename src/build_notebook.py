"""Generate and execute the reader-facing analysis notebook."""

from __future__ import annotations

import os
import base64
import contextlib
import io
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "analysis.ipynb"
PROCESSED = ROOT / "data" / "processed"


def build() -> Path:
    import nbformat as nbf
    from nbclient import NotebookClient

    summary = pd.read_csv(PROCESSED / "scenario_summary.csv").set_index("scenario")
    frontier = pd.read_csv(PROCESSED / "protein_frontier.csv")
    balanced = summary.loc["balanced"]
    convenience = summary.loc["convenience"]
    high_protein = summary.loc["high_protein"]
    protein_delta = float(frontier.iloc[-1].weekly_cost_eur - frontier.iloc[0].weekly_cost_eur)

    notebook = nbf.v4.new_notebook()
    notebook.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata.language_info = {"name": "python", "version": "3.12"}
    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# Protein Thinking: Cost-Constrained Student Meal Planning\n\n"
            "## tl;dr\n\n"
            f"The balanced model finds a **€{balanced.weekly_cost_eur:.2f}** illustrative weekly basket "
            f"with **{balanced.average_protein_g:.1f} g average protein per day** and "
            f"**{int(balanced.unique_foods)} distinct foods**. Raising the protein floor from 130 g to "
            f"210 g adds **€{protein_delta:.2f} per week** under the same catalogue and constraints. "
            f"The convenience scenario limits active preparation to {convenience.average_prep_minutes:.0f} "
            f"minutes per day and costs €{convenience.weekly_cost_eur:.2f}."
        ),
        nbf.v4.new_markdown_cell(
            "## Context & Methods\n\n"
            "**Decision question:** What is the lowest-cost seven-day grocery basket that satisfies a "
            "chosen average nutrition target while remaining varied and practical?\n\n"
            "The analysis uses two mixed-integer stages. Stage 1 minimises basket cost subject to weekly "
            "nutrition, variety, food-frequency and preparation constraints. Stage 2 fixes that basket "
            "and allocates servings across seven days to reduce day-to-day variation.\n\n"
            "### Key Assumptions\n\n"
            "- Prices are illustrative Dutch retail assumptions, not a live supermarket feed.\n"
            "- Nutrition values are representative product-label values.\n"
            "- Nutrition constraints apply to the weekly average; the daily schedule is illustrative.\n"
            "- The model is a portfolio demonstration, not dietary or medical advice."
        ),
        nbf.v4.new_markdown_cell("## Data"),
        nbf.v4.new_code_cell(
            "import os\n"
            "from pathlib import Path\n\n"
            "os.environ.setdefault('MPLCONFIGDIR', '/tmp/protein-thinking-matplotlib')\n"
            "import matplotlib\n"
            "matplotlib.use('Agg')\n"
            "import matplotlib.pyplot as plt\n"
            "import pandas as pd\n\n"
            "ROOT = Path.cwd()\n"
            "PROCESSED = ROOT / 'data' / 'processed'\n"
            "summary = pd.read_csv(PROCESSED / 'scenario_summary.csv')\n"
            "frontier = pd.read_csv(PROCESSED / 'protein_frontier.csv')\n"
            "daily = pd.read_csv(PROCESSED / 'daily_summary.csv')\n"
            "grocery = pd.read_csv(PROCESSED / 'grocery_list.csv')\n"
            "print(summary[['scenario_label', 'weekly_cost_eur', 'average_protein_g', "
            "'average_prep_minutes', 'unique_foods']].to_string(index=False))"
        ),
        nbf.v4.new_markdown_cell("### Validate the analytical outputs"),
        nbf.v4.new_code_cell(
            "assert summary['solver_mip_gap'].fillna(0).le(0.001).all()\n"
            "assert daily.groupby('scenario')['day'].nunique().eq(7).all()\n"
            "assert frontier['protein_floor_g'].is_monotonic_increasing\n"
            "assert frontier['weekly_cost_eur'].is_monotonic_increasing\n"
            "print('Core reconciliation and optimisation checks passed.')"
        ),
        nbf.v4.new_markdown_cell("## Results\n\n### Scenario comparison"),
        nbf.v4.new_code_cell(
            "plot_data = summary.sort_values('weekly_cost_eur')\n"
            "colors = ['#d9a441' if label == 'Balanced' else '#4d7a62' for label in plot_data['scenario_label']]\n"
            "fig, ax = plt.subplots(figsize=(9, 4.6))\n"
            "bars = ax.barh(plot_data['scenario_label'], plot_data['weekly_cost_eur'], color=colors)\n"
            "ax.bar_label(bars, labels=[f'€{value:.2f}' for value in plot_data['weekly_cost_eur']], padding=5)\n"
            "ax.set(title='Illustrative weekly basket cost by scenario', xlabel='Euros per seven-day basket')\n"
            "ax.spines[['top', 'right', 'left']].set_visible(False)\n"
            "ax.grid(axis='x', alpha=.2)\n"
            "ax.set_axisbelow(True)\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("### Protein-cost sensitivity"),
        nbf.v4.new_code_cell(
            "fig, ax = plt.subplots(figsize=(9, 4.6))\n"
            "ax.plot(frontier['protein_floor_g'], frontier['weekly_cost_eur'], color='#254f3d', linewidth=3, marker='o')\n"
            "ax.set(title='Protein-cost sensitivity', xlabel='Minimum average protein per day (g)', "
            "ylabel='Minimum weekly basket cost (€)')\n"
            "ax.grid(alpha=.2)\n"
            "ax.spines[['top', 'right']].set_visible(False)\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("### Balanced grocery basket"),
        nbf.v4.new_code_cell(
            "balanced_grocery = (grocery[grocery['scenario'] == 'balanced']\n"
            "    .sort_values('weekly_cost_eur', ascending=False)\n"
            "    [['food_name', 'category', 'servings', 'weekly_cost_eur']])\n"
            "print(balanced_grocery.head(12).to_string(index=False))"
        ),
        nbf.v4.new_markdown_cell(
            "## Takeaways\n\n"
            f"1. **Protein is a measurable cost driver.** Moving from 130 g to 210 g adds "
            f"€{protein_delta:.2f} per illustrative week.\n"
            f"2. **Convenience has a premium.** The 35-minute preparation cap produces a "
            f"€{convenience.weekly_cost_eur:.2f} basket, €{convenience.weekly_cost_eur-balanced.weekly_cost_eur:.2f} "
            "above the balanced case.\n"
            f"3. **The high-protein constraint changes the purchasing decision.** The 190 g scenario "
            f"costs €{high_protein.weekly_cost_eur:.2f}, compared with €{balanced.weekly_cost_eur:.2f} "
            "for the balanced scenario.\n\n"
            "These are optimisation outputs under a controlled illustrative catalogue. A real decision "
            "would require current product prices, verified labels and personalised requirements."
        ),
    ]

    # The normal route is nbclient. This workspace blocks the local sockets a
    # Jupyter kernel requires, so the repository also carries an in-process
    # fallback that runs the exact same cells sequentially and embeds outputs.
    try:
        client = NotebookClient(
            notebook,
            timeout=180,
            kernel_name="python3",
            resources={"metadata": {"path": str(ROOT)}},
        )
        client.execute()
        notebook.metadata.execution_mode = "nbclient"
    except RuntimeError as error:
        if "Kernel died before replying" not in str(error):
            raise
        namespace: dict = {"__name__": "__main__"}
        execution_count = 0
        previous_directory = Path.cwd()
        os.chdir(ROOT)
        try:
            for cell in notebook.cells:
                if cell.cell_type != "code":
                    continue
                execution_count += 1
                cell.execution_count = execution_count
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    exec(compile(cell.source, f"notebook-cell-{execution_count}", "exec"), namespace)
                outputs = []
                if stream.getvalue():
                    outputs.append(nbf.v4.new_output("stream", name="stdout", text=stream.getvalue()))
                if "plt.show()" in cell.source:
                    buffer = io.BytesIO()
                    namespace["plt"].gcf().savefig(buffer, format="png", dpi=130, bbox_inches="tight")
                    outputs.append(
                        nbf.v4.new_output(
                            "display_data",
                            data={"image/png": base64.b64encode(buffer.getvalue()).decode("ascii")},
                            metadata={},
                        )
                    )
                    namespace["plt"].close("all")
                cell.outputs = outputs
        finally:
            os.chdir(previous_directory)
        notebook.metadata.execution_mode = "in-process fallback; kernel sockets unavailable"
    nbf.write(notebook, OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    os.environ.setdefault("JUPYTER_CONFIG_DIR", "/tmp/protein-thinking-jupyter")
    print(build())
