import os
import sys
import yaml
import json
import time
import argparse
from transformers import (
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from src.data.data_loader import DataLoader
from src.data.process_sum import SumProcessor
from src.models.build_sum import SumModelBuilder
from src.metrics.metric_sum import SumMetrics


def evaluate_summarization(config_path):
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    run_name = os.path.basename(config_path).replace(".yaml", "")
    best_model_path = os.path.join(cfg["training"]["output_dir"], "best")

    print(f"[INFO] Bat dau danh gia tap Test cho: {run_name}")

    if not os.path.exists(best_model_path):
        raise FileNotFoundError(
            f"Khong tim thay model da train tai {best_model_path}"
        )

    is_bartpho_word = "bartpho-word" in cfg["model"]["name"].lower()
    model, tokenizer = SumModelBuilder.build(best_model_path)

    dataset = DataLoader.load(cfg["data"]["train_path"].replace("/train", ""))

    # Giới hạn test samples nếu có config
    max_test = cfg["data"].get("max_test_samples", None)
    if max_test and len(dataset["test"]) > max_test:
        dataset["test"] = dataset["test"].shuffle(seed=42).select(range(max_test))

    processor = SumProcessor(
        tokenizer,
        max_input_length=cfg["model"]["max_input_length"],
        max_target_length=cfg["model"]["max_target_length"],
        word_segment=is_bartpho_word,
    )

    print(f"[INFO] Dang ma hoa {len(dataset['test'])} mau Test...")
    test_ds = dataset["test"].map(
        processor.process,
        batched=True,
        num_proc=4,
        remove_columns=dataset["test"].column_names,
    )

    eval_args = Seq2SeqTrainingArguments(
        output_dir=cfg["training"]["output_dir"],
        predict_with_generate=True,
        per_device_eval_batch_size=cfg.get("evaluation", {}).get("batch_size", 8),
        bf16=cfg.get("bf16", True),
        report_to="none",
    )

    metrics = SumMetrics(tokenizer)

    trainer = Seq2SeqTrainer(
        model=model,
        args=eval_args,
        eval_dataset=test_ds,
        processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
        compute_metrics=metrics.compute,
    )

    print("[INFO] Dang thuc thi Generation tren tap Test...")
    start_time = time.time()
    results = trainer.evaluate(
        metric_key_prefix="test",
        max_length=cfg["model"]["max_target_length"],
        num_beams=cfg.get("evaluation", {}).get("generation_num_beams", 4),
    )
    inference_time = time.time() - start_time

    results["total_inference_time_sec"] = round(inference_time, 2)
    results["samples_per_second"] = round(len(test_ds) / inference_time, 2)

    report_path = os.path.join(
        ROOT_DIR, "results", "logs", f"{run_name}_test_report.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("[INFO] KET QUA TEST:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print(f"[INFO] Da luu bao cao vao {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    evaluate_summarization(args.config)