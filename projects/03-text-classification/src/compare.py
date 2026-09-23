#!/usr/bin/env python3
"""Merge BERT + LLM metric JSON into a markdown comparison table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bert", default="results/bert/metrics.json")
    ap.add_argument("--llm", default="results/llm_metrics.json")
    ap.add_argument("--out", default="results/comparison.md")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    bert = load(root / args.bert)
    llm = load(root / args.llm)

    lines = [
        "# BERT vs LLM classification",
        "",
        "| Method | Model | Accuracy | Macro-F1 | Notes |",
        "|--------|-------|----------|----------|-------|",
        (
            f"| BERT | {bert.get('model')} | {bert['test']['accuracy']:.4f} | "
            f"{bert['test']['macro_f1']:.4f} | val_best_macro_f1={bert.get('val_best_macro_f1')} |"
        ),
        (
            f"| LLM | {llm.get('model')} | {llm['accuracy']:.4f} | {llm['macro_f1']:.4f} | "
            f"few_shot/label={llm.get('few_shot_per_label')} "
            f"parse_fail={llm.get('parse_fail_rate'):.2%} "
            f"seconds={llm.get('seconds'):.1f} |"
        ),
        "",
        "Same test split; labels fixed. Prefer macro-F1 when classes are imbalanced.",
        "",
    ]
    out = root / args.out
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out.read_text())


if __name__ == "__main__":
    main()
