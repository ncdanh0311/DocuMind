import os
import sys
import yaml
import argparse
from transformers import (
    TrainingArguments,
    Trainer,
    DefaultDataCollator,
    EarlyStoppingCallback,
)
 
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)
 
from src.data.data_loader import DataLoader
from src.data.process_qa import QAProcessor
from src.models.build_qa import QAModelBuilder
from src.metrics.metric_qa import QAMetrics
from src.logger import ResearchLogger
 
 
def _get_num_proc(model_name: str) -> int:
    """
    PhoBERT fast tokenizer (Rust-based) + multiprocessing hay bị deadlock.
    XLM-R an toàn với num_proc=4.
 
    Nguồn: HuggingFace docs khuyến nghị num_proc=1 khi tokenizer
    dùng Rust threading để tránh conflict với Python multiprocessing.
    """
    if "phobert" in model_name.lower():
        print("[INFO] PhoBERT → num_proc=1 (tranh deadlock fast tokenizer)")
        return 1
    print("[INFO] XLM-R → num_proc=4")
    return 4
 
 
def train_qa(config_path: str):
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
 
    run_name = os.path.basename(config_path).replace(".yaml", "")
    model_name = cfg["model"]["name"]
 
    # ── Model & Tokenizer (có assert is_fast bên trong) ──────────────────────
    model, tokenizer = QAModelBuilder.build(model_name, cache_dir=cfg.get("cache_dir", "./hf_cache"))
 
    # ── Dataset ──────────────────────────────────────────────────────────────
    dataset = DataLoader.load(
        cfg["data"]["train_path"].replace("/train", "")
    )
 
    processor = QAProcessor(
        tokenizer,
        max_length=cfg["model"]["max_length"],
        doc_stride=cfg["model"]["doc_stride"],
    )
 
    # ── Tokenize — num_proc an toàn theo model ────────────────────────────────
    num_proc = _get_num_proc(model_name)
    print(f"[INFO] Tokenizing du lieu QA (num_proc={num_proc})...")
 
    tokenized_ds = dataset.map(
        processor.process,
        batched=True,
        num_proc=num_proc,
        remove_columns=dataset["train"].column_names,
    )
 
    # ── Training Arguments ───────────────────────────────────────────────────
    args = TrainingArguments(
        output_dir=cfg["training"]["output_dir"],
        num_train_epochs=cfg["training"]["num_train_epochs"],
 
        per_device_train_batch_size=cfg["data"]["batch_size"],
        per_device_eval_batch_size=cfg["evaluation"].get("batch_size", 32),
 
        learning_rate=float(cfg["training"]["learning_rate"]),
        weight_decay=cfg["training"].get("weight_decay", 0.01),
        warmup_ratio=cfg["training"].get("warmup_ratio", 0.1),
        max_grad_norm=cfg["training"].get("max_grad_norm", 1.0),
 
        gradient_accumulation_steps=cfg["training"].get(
            "gradient_accumulation_steps", 1
        ),
 
        # cosine tốt hơn linear ~0.5–1% F1 trên QA task
        lr_scheduler_type="cosine",
 
        bf16=cfg.get("bf16", True),
        fp16=cfg.get("fp16", False),
 
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
 
        load_best_model_at_end=True,
        metric_for_best_model="eval_f1",
        greater_is_better=True,        # F1 cao hơn = tốt hơn
 
        save_total_limit=1,
 
        # num_workers: PhoBERT dùng ít hơn để tránh conflict
        dataloader_num_workers=cfg["data"].get("num_workers", 2),
 
        remove_unused_columns=True,
        report_to="none",
        seed=cfg.get("seed", 42),
    )
 
    # ── Trainer ──────────────────────────────────────────────────────────────
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized_ds["train"],
        eval_dataset=tokenized_ds["validation"],
        processing_class=tokenizer,
        data_collator=DefaultDataCollator(),
        compute_metrics=QAMetrics.compute,
        callbacks=[
            ResearchLogger(
                os.path.join(ROOT_DIR, "results", "logs", f"{run_name}_history.csv"),
                metric_for_best="eval_f1",
                greater_is_better=True,
            ),
            EarlyStoppingCallback(
                early_stopping_patience=cfg["training"].get(
                    "early_stopping_patience", 3
                )
            ),
        ],
    )
 
    print(f"[START] Training QA: {run_name}")
    trainer.train()
 
    # ── Evaluate on Test ─────────────────────────────────────────────────────
    print("\n[TEST] Danh gia tap Test...")
    test_results = trainer.evaluate(
        tokenized_ds["validation"],
        metric_key_prefix="test",
    )
 
    result_path = os.path.join(
        ROOT_DIR, "results", "logs", f"{run_name}_results.txt"
    )
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, "a", encoding="utf-8") as f:
        f.write("\n=== KET QUA TEST CUOI CUNG (QA) ===\n")
        for k, v in test_results.items():
            f.write(f"{k.upper()}: {v}\n")
 
    trainer.save_model(
        os.path.join(cfg["training"]["output_dir"], "best_model")
    )
    print(f"[DONE] Best model: {cfg['training']['output_dir']}/best_model")
 
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    train_qa(args.config)
 