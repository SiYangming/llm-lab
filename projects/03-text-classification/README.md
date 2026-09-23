# 03 — Text classification: BERT vs LLM

Part of [llm-lab](https://github.com/SiYangming/llm-lab) (八斗 AI Project 3).

同一测试集上对比：**编码器微调（BERT/DistilBERT）** vs **LLM 零样本/少样本分类**。

## What you get

| Script | Role |
|--------|------|
| `src/train_bert.py` | Fine-tune DistilBERT (default), pick best val macro-F1, report **test once** |
| `src/infer_llm.py` | Zero/few-shot LLM classify with label parsing + retries |
| `src/compare.py` | Merge metrics into `results/comparison.md` |
| `data/sample/*.csv` | Tiny 3-class smoke dataset (`text,label`) |

## Setup

From **repo root**:

```bash
cd llm-lab
source venv/bin/activate
pip install -r requirements.txt
pip install -r projects/03-text-classification/requirements.txt
cp projects/03-text-classification/.env.example projects/03-text-classification/.env
# fill LLM_API_KEY for the LLM path
```

## Run (sample data)

```bash
cd llm-lab
source venv/bin/activate

# 1) BERT baseline (CPU ok on tiny sample)
PYTHONPATH=projects/03-text-classification python -m src.train_bert \
  --train data/sample/train.csv --val data/sample/val.csv --test data/sample/test.csv

# 2) LLM zero-shot on same test
PYTHONPATH=projects/03-text-classification python -m src.infer_llm --few-shot 0

# optional few-shot (1 example per label from train)
PYTHONPATH=projects/03-text-classification python -m src.infer_llm --few-shot 1

# 3) comparison table
PYTHONPATH=projects/03-text-classification python -m src.compare
```

Paths inside the scripts are relative to `projects/03-text-classification/`.

## Your own data

CSV with headers `text,label`. Keep the **same label set** and a held-out `test.csv` you never tune on.

## Resume bullets

- Compared encoder fine-tuning vs LLM zero/few-shot classification on the same test split with accuracy and macro-F1.
- Implemented label-constrained LLM decoding via prompt + parse/retry, and reported parse-fail rate alongside quality metrics.

中文：

- 在同一测试集上对比 BERT 类微调与 LLM 零/少样本分类，报告 accuracy 与 macro-F1。
- 为 LLM 路径做标签约束（prompt + 解析重试），并统计解析失败率与耗时。

## License

MIT (see repo root).
