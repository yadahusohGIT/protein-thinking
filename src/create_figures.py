"""Create the summary charts used in the README."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/protein-thinking-matplotlib")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
ASSETS = ROOT / "assets"


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.facecolor": "#fffdf8",
            "figure.facecolor": "#fffdf8",
            "axes.edgecolor": "#cfc9ba",
            "axes.labelcolor": "#657169",
            "xtick.color": "#657169",
            "ytick.color": "#657169",
            "text.color": "#17211b",
        }
    )


def build() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    style()
    summary = pd.read_csv(PROCESSED / "scenario_summary.csv").sort_values("weekly_cost_eur")
    frontier = pd.read_csv(PROCESSED / "protein_frontier.csv")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    colors = ["#d9a441" if value == "Balanced" else "#4d7a62" for value in summary["scenario_label"]]
    bars = ax.barh(summary["scenario_label"], summary["weekly_cost_eur"], color=colors)
    ax.bar_label(bars, labels=[f"€{v:.2f}" for v in summary["weekly_cost_eur"]], padding=6, fontsize=10)
    ax.set_title("Illustrative weekly basket cost by scenario", loc="left", fontsize=16, fontweight="bold")
    ax.set_xlabel("Euros per seven-day basket")
    ax.set_xlim(0, summary["weekly_cost_eur"].max() * 1.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#e7e2d8")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(ASSETS / "scenario_costs.svg", format="svg", bbox_inches="tight")
    fig.savefig(ASSETS / "scenario_costs.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(frontier["protein_floor_g"], frontier["weekly_cost_eur"], color="#254f3d", linewidth=3)
    ax.scatter(frontier["protein_floor_g"], frontier["weekly_cost_eur"], color="#fffdf8", edgecolor="#254f3d", linewidth=2, s=55, zorder=3)
    ax.scatter([160], [frontier.loc[frontier["protein_floor_g"] == 160, "weekly_cost_eur"].iloc[0]], color="#d9a441", edgecolor="#254f3d", linewidth=2, s=75, zorder=4)
    ax.set_title("Protein-cost sensitivity", loc="left", fontsize=16, fontweight="bold")
    ax.set_xlabel("Minimum average protein per day (g)")
    ax.set_ylabel("Minimum weekly basket cost (€)")
    ax.grid(color="#e7e2d8")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(ASSETS / "protein_cost_frontier.svg", format="svg", bbox_inches="tight")
    fig.savefig(ASSETS / "protein_cost_frontier.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    build()
