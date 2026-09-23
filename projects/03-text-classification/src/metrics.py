"""Classification metrics shared by BERT and LLM paths."""

from __future__ import annotations

from sklearn.metrics import accuracy_score, classification_report, f1_score


def summarize(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "report": classification_report(
            y_true, y_pred, labels=labels, digits=4, zero_division=0
        ),
    }


def print_summary(name: str, summary: dict) -> None:
    print(f"\n=== {name} ===")
    print(f"accuracy={summary['accuracy']:.4f}  macro_f1={summary['macro_f1']:.4f}")
    print(summary["report"])
