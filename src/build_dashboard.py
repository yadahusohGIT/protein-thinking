"""Build the self-contained interactive dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TEMPLATE = ROOT / "dashboard" / "template.html"
OUTPUT = ROOT / "dashboard" / "index.html"


def records(name: str) -> list[dict]:
    frame = pd.read_csv(PROCESSED / f"{name}.csv")
    return json.loads(frame.to_json(orient="records"))


def build() -> Path:
    # Embedding the data keeps the dashboard usable as a single HTML file,
    # without a web server or separate API.
    payload = {
        "summary": records("scenario_summary"),
        "daily": records("daily_summary"),
        "plan": records("meal_plan"),
        "grocery": records("grocery_list"),
        "frontier": records("protein_frontier"),
    }
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "__PROTEIN_THINKING_DATA__",
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
    )
    OUTPUT.write_text(html, encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    print(build())
