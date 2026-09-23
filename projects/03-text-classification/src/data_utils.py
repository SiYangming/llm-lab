"""Load CSV datasets with columns: text,label."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED = ("text", "label")


def load_split(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")
    df = df.dropna(subset=list(REQUIRED)).copy()
    df["text"] = df["text"].astype(str)
    df["label"] = df["label"].astype(str)
    return df.reset_index(drop=True)


def label_list(*frames: pd.DataFrame) -> list[str]:
    labels: set[str] = set()
    for df in frames:
        labels.update(df["label"].unique().tolist())
    return sorted(labels)
