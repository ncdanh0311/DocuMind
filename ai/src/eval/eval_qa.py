
import os
import sys
import yaml
import json
import time
import argparse
from transformers import (
    Trainer,
    TrainingArguments,
    DefaultDataCollator,
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from src.data.data_loader import DataLoader
from src.data.process_qa import QAProcessor
from src.models.build_qa import QAModelBuilder
from src.metrics.metric_qa import QAMetrics


def evaluate_qa(config_path: str):
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    run_name        = os.path.basename(config_path).replace(".yaml", "")
    best_model_path = os.path.join(cfg["training"]["output_dir"], "best_model")

    print(f"[INFO] Danh gia tap Test: {run_name}")
    print(f"[INFO] Best model: {best_model_path}")

    if not os.path.exists(best_model_path):
        raise FileNotFoundError(f"Khong tim thay model tai {best_model_path}")

    # ── Load model đã train ──────────────────────────────────────────────────
    model, tokenizer = QAModelBuilder.build(best_model_path)

    # ── Load & tokenize tập Test ─────────────────────────────────────────────
    dataset = DataLoader.load(
        cfg["data"]["train_path"].replace("/train", "")
    )

    max_test = cfg["data"].get("max_test_samples", None)
    if max_test and len(dataset["test"]) > max_test:
        dataset["test"] = dataset["test"].shuffle(seed=42).select(range(max_test))

    processor = QAProcessor(
        tokenizer,
        max_length=cfg["model"]["max_length"],
        doc_stride=cfg["model"]["doc_stride"],
    )

    print(f"[INFO] Ma hoa {len(dataset['validation'])} mau Validation...")
    validation_ds = dataset["validation"].map(
        processor.process,
        batched=True,
        num_proc=1,
        remove_columns=dataset["test"].column_names,
    )

    # ── Eval args ────────────────────────────────────────────────────────────
    eval_args = TrainingArguments(
        output_dir=cfg["training"]["output_dir"],
        per_device_eval_batch_size=cfg.get("evaluation", {}).get("batch_size", 32),
        bf16=cfg.get("bf16", True),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=eval_args,
        eval_dataset=validation_ds,
        processing_class=tokenizer,
        data_collator=DefaultDataCollator(),
        compute_metrics=QAMetrics.compute,
    )

    # ── Inference ────────────────────────────────────────────────────────────
    print("[INFO] Inference tren tap Validation...")
    start_time = time.time()
    results    = trainer.evaluate(metric_key_prefix="test")
    elapsed    = time.time() - start_time

    results["total_inference_time_sec"] = round(elapsed, 2)
    results["samples_per_second"]       = round(len(validation_ds) / elapsed, 2)

    # ── Lưu báo cáo ─────────────────────────────────────────────────────────
    report_path = os.path.join(
        ROOT_DIR, "results", "logs", f"{run_name}_test_report.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\n[INFO] KET QUA TEST:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print(f"[INFO] Bao cao luu tai: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    evaluate_qa(args.config)