#!/usr/bin/env python3
"""Zero-shot (optional few-shot) LLM classification on the same test split."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .data_utils import label_list, load_split
from .metrics import print_summary, summarize


def build_prompt(text: str, labels: list[str], few_shot: list[tuple[str, str]] | None) -> list[dict[str, str]]:
    label_line = ", ".join(labels)
    system = (
        "You are a text classifier. Reply with EXACTLY one label from the allowed list. "
        "No punctuation, no explanation."
    )
    user_parts = [f"Allowed labels: {label_line}"]
    if few_shot:
        user_parts.append("Examples:")
        for t, y in few_shot:
            user_parts.append(f"Text: {t}\nLabel: {y}")
    user_parts.append(f"Text: {text}\nLabel:")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]


def parse_label(raw: str, labels: list[str]) -> str | None:
    s = raw.strip().strip('"').strip("'")
    # exact
    for lab in labels:
        if s.lower() == lab.lower():
            return lab
    # find a label token inside response
    for lab in labels:
        if re.search(rf"\b{re.escape(lab)}\b", s, flags=re.I):
            return lab
    return None


def classify_one(client: OpenAI, model: str, text: str, labels: list[str], few_shot, max_retries: int) -> str:
    messages = build_prompt(text, labels, few_shot)
    last = ""
    for attempt in range(max_retries + 1):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=16,
        )
        last = (resp.choices[0].message.content or "").strip()
        parsed = parse_label(last, labels)
        if parsed is not None:
            return parsed
        # reinforce
        messages = messages + [
            {"role": "assistant", "content": last},
            {"role": "user", "content": f"Invalid. Reply with exactly one of: {', '.join(labels)}"},
        ]
        time.sleep(0.2 * (attempt + 1))
    return "__PARSE_FAIL__"


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/sample/train.csv")
    ap.add_argument("--test", default="data/sample/test.csv")
    ap.add_argument("--few-shot", type=int, default=0, help="examples per label from train")
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--limit", type=int, default=0, help="optional cap on test rows")
    ap.add_argument("--out", default="results/llm_metrics.json")
    args = ap.parse_args()

    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Set LLM_API_KEY in .env (see .env.example)")

    root = Path(__file__).resolve().parents[1]
    train_df = load_split(root / args.train)
    test_df = load_split(root / args.test)
    if args.limit > 0:
        test_df = test_df.head(args.limit)
    labels = label_list(train_df, test_df)

    few_shot: list[tuple[str, str]] | None = None
    if args.few_shot > 0:
        few_shot = []
        for lab in labels:
            sub = train_df[train_df["label"] == lab].head(args.few_shot)
            few_shot.extend((r.text, r.label) for r in sub.itertuples())

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip(),
    )
    model = os.getenv("LLM_MODEL", "deepseek-chat").strip() or "deepseek-chat"

    y_true, y_pred = [], []
    t0 = time.time()
    for row in test_df.itertuples():
        pred = classify_one(client, model, row.text, labels, few_shot, args.max_retries)
        y_true.append(row.label)
        y_pred.append(pred)
        print(f"gold={row.label} pred={pred} | {row.text[:60]}")

    # map parse fails for metrics: keep as distinct miss
    labels_for_metric = labels + (["__PARSE_FAIL__"] if "__PARSE_FAIL__" in y_pred else [])
    summary = summarize(y_true, y_pred, labels)
    print_summary("LLM test", summary)
    elapsed = time.time() - t0

    out = {
        "model": model,
        "few_shot_per_label": args.few_shot,
        "n_test": len(y_true),
        "seconds": elapsed,
        "parse_fail_rate": y_pred.count("__PARSE_FAIL__") / max(len(y_pred), 1),
        "accuracy": summary["accuracy"],
        "macro_f1": summary["macro_f1"],
        "labels": labels,
    }
    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
