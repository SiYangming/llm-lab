#!/usr/bin/env python3
"""Fine-tune a small encoder for text classification (baseline)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from .data_utils import label_list, load_split
from .metrics import print_summary, summarize


class TextClsDataset(Dataset):
    def __init__(self, texts, label_ids, tokenizer, max_length: int):
        self.texts = texts
        self.label_ids = label_ids
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int):
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(self.label_ids[idx], dtype=torch.long)
        return item


def encode_labels(series, label2id):
    return [label2id[x] for x in series.tolist()]


@torch.no_grad()
def evaluate(model, loader, device, id2label, labels):
    model.eval()
    y_true, y_pred = [], []
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items()}
        logits = model(**batch).logits
        pred = logits.argmax(dim=-1).tolist()
        true = batch["labels"].tolist()
        y_pred.extend(id2label[i] for i in pred)
        y_true.extend(id2label[i] for i in true)
    return summarize(y_true, y_pred, labels)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/sample/train.csv")
    ap.add_argument("--val", default="data/sample/val.csv")
    ap.add_argument("--test", default="data/sample/test.csv")
    ap.add_argument("--model", default="distilbert-base-uncased")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-length", type=int, default=64)
    ap.add_argument("--out", default="results/bert")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    train_df = load_split(root / args.train)
    val_df = load_split(root / args.val)
    test_df = load_split(root / args.test)
    labels = label_list(train_df, val_df, test_df)
    label2id = {l: i for i, l in enumerate(labels)}
    id2label = {i: l for l, i in label2id.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(labels), id2label=id2label, label2id=label2id
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    train_ds = TextClsDataset(
        train_df["text"].tolist(), encode_labels(train_df["label"], label2id), tokenizer, args.max_length
    )
    val_ds = TextClsDataset(
        val_df["text"].tolist(), encode_labels(val_df["label"], label2id), tokenizer, args.max_length
    )
    test_ds = TextClsDataset(
        test_df["text"].tolist(), encode_labels(test_df["label"], label2id), tokenizer, args.max_length
    )
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size)

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total_steps = max(len(train_loader) * args.epochs, 1)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * total_steps), total_steps)

    best_f1, best_state = -1.0, None
    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for batch in tqdm(train_loader, desc=f"epoch {epoch}"):
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(**batch)
            out.loss.backward()
            opt.step()
            sched.step()
            opt.zero_grad()
            losses.append(out.loss.item())
        val_sum = evaluate(model, val_loader, device, id2label, labels)
        print(f"epoch={epoch} train_loss={sum(losses)/len(losses):.4f} val_macro_f1={val_sum['macro_f1']:.4f}")
        if val_sum["macro_f1"] >= best_f1:
            best_f1 = val_sum["macro_f1"]
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    test_sum = evaluate(model, test_loader, device, id2label, labels)
    print_summary("BERT test", test_sum)

    out_dir = root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)
    metrics_path = out_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            {"model": args.model, "labels": labels, "val_best_macro_f1": best_f1, "test": {
                "accuracy": test_sum["accuracy"], "macro_f1": test_sum["macro_f1"]
            }},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"saved model + metrics -> {out_dir}")


if __name__ == "__main__":
    main()
