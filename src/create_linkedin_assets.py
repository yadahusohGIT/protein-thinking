"""Create a three-image LinkedIn set for the Protein Thinking project."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/protein-thinking-matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PROCESSED = ROOT / "data" / "processed"

INK = "#17211b"
MUTED = "#657169"
PAPER = "#fffdf8"
GREEN = "#254f3d"
GREEN_MID = "#4d7a62"
GOLD = "#d9a441"
GRID = "#e7e2d8"


def new_figure(background: str = PAPER) -> tuple[plt.Figure, plt.Axes]:
    figure = plt.figure(figsize=(16, 9), dpi=100, facecolor=background)
    axis = figure.add_axes([0, 0, 1, 1])
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    return figure, axis


def save(figure: plt.Figure, name: str) -> None:
    figure.savefig(ASSETS / name, dpi=100, facecolor=figure.get_facecolor(), edgecolor="none")
    plt.close(figure)


def cover() -> None:
    figure, axis = new_figure(GREEN)
    axis.add_patch(Circle((0.93, 1.02), 0.25, color=GOLD, alpha=0.95))
    axis.add_patch(Circle((0.93, 1.02), 0.14, color=GREEN, alpha=1))

    axis.text(0.07, 0.85, "BUSINESS ANALYTICS PROJECT", color=GOLD, fontsize=17, fontweight="bold")
    axis.text(0.07, 0.66, "Protein\nThinking", color=PAPER, fontsize=76, fontweight="bold", linespacing=0.88)
    axis.text(
        0.07,
        0.48,
        "Finding a low-cost weekly food basket\nwith mixed-integer programming",
        color="#dbe7de",
        fontsize=27,
        linespacing=1.35,
    )

    metrics = [
        ("€44.37", "balanced weekly cost"),
        ("160.1 g", "average protein / day"),
        ("18", "different foods"),
    ]
    x_positions = [0.07, 0.34, 0.61]
    for x, (value, label) in zip(x_positions, metrics):
        axis.add_patch(
            FancyBboxPatch(
                (x, 0.14),
                0.23,
                0.19,
                boxstyle="round,pad=0.012,rounding_size=0.02",
                facecolor="#315f4a",
                edgecolor="#5f826f",
                linewidth=1.5,
            )
        )
        axis.text(x + 0.02, 0.235, value, color=PAPER, fontsize=31, fontweight="bold")
        axis.text(x + 0.02, 0.175, label, color="#cbd9cf", fontsize=15)

    axis.text(0.93, 0.08, "Yadah Usoh", color="#cbd9cf", fontsize=16, ha="right")
    save(figure, "linkedin_1_cover.png")


def scenario_chart(summary: pd.DataFrame) -> None:
    figure = plt.figure(figsize=(16, 9), dpi=100, facecolor=PAPER)
    axis = figure.add_axes([0.15, 0.16, 0.77, 0.68])
    ordered = summary.sort_values("weekly_cost_eur")
    colors = [GOLD if label == "Balanced" else GREEN_MID for label in ordered["scenario_label"]]
    bars = axis.barh(ordered["scenario_label"], ordered["weekly_cost_eur"], color=colors, height=0.62)
    axis.bar_label(
        bars,
        labels=[f"€{value:.2f}" for value in ordered["weekly_cost_eur"]],
        padding=12,
        fontsize=19,
        color=INK,
    )
    axis.set_xlim(0, 61)
    axis.set_xlabel("Example cost for a seven-day basket", fontsize=17, color=MUTED, labelpad=15)
    axis.tick_params(axis="x", labelsize=15, colors=MUTED)
    axis.tick_params(axis="y", labelsize=20, colors=INK, pad=10)
    axis.grid(axis="x", color=GRID, linewidth=1.2)
    axis.set_axisbelow(True)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_color("#cfc9ba")
    figure.text(0.07, 0.92, "Protein Thinking", color=GREEN_MID, fontsize=16, fontweight="bold")
    figure.text(0.07, 0.855, "Weekly basket cost by scenario", color=INK, fontsize=34, fontweight="bold")
    figure.text(0.07, 0.055, "Example prices, not a live supermarket comparison", color=MUTED, fontsize=14)
    save(figure, "linkedin_2_scenarios.png")


def frontier_chart(frontier: pd.DataFrame) -> None:
    figure = plt.figure(figsize=(16, 9), dpi=100, facecolor=PAPER)
    axis = figure.add_axes([0.11, 0.17, 0.82, 0.65])
    axis.plot(
        frontier["protein_floor_g"],
        frontier["weekly_cost_eur"],
        color=GREEN,
        linewidth=4,
        marker="o",
        markersize=10,
        markerfacecolor=PAPER,
        markeredgewidth=3,
    )
    balanced = frontier.loc[frontier["protein_floor_g"] == 160].iloc[0]
    axis.scatter([160], [balanced.weekly_cost_eur], s=180, color=GOLD, edgecolor=GREEN, linewidth=3, zorder=4)
    axis.annotate(
        "Balanced target",
        xy=(160, balanced.weekly_cost_eur),
        xytext=(150, balanced.weekly_cost_eur + 4.7),
        fontsize=16,
        color=INK,
        arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 1.5},
    )
    axis.set_xlabel("Minimum average protein per day (g)", fontsize=17, color=MUTED, labelpad=15)
    axis.set_ylabel("Minimum weekly basket cost (€)", fontsize=17, color=MUTED, labelpad=15)
    axis.tick_params(labelsize=15, colors=MUTED)
    axis.grid(color=GRID, linewidth=1.2)
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["bottom", "left"]].set_color("#cfc9ba")
    figure.text(0.07, 0.92, "Protein Thinking", color=GREEN_MID, fontsize=16, fontweight="bold")
    figure.text(0.07, 0.855, "The cost of increasing the protein target", color=INK, fontsize=34, fontweight="bold")
    figure.text(
        0.07,
        0.055,
        "The 130 g to 210 g increase added €19.76 per week in the example model",
        color=MUTED,
        fontsize=14,
    )
    save(figure, "linkedin_3_protein_cost.png")


def build() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    summary = pd.read_csv(PROCESSED / "scenario_summary.csv")
    frontier = pd.read_csv(PROCESSED / "protein_frontier.csv")
    cover()
    scenario_chart(summary)
    frontier_chart(frontier)


if __name__ == "__main__":
    build()
