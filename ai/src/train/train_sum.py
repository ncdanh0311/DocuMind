#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path
from datasets import load_from_disk
from transformers import (
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    EarlyStoppingCallback,
)

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai.src.models.build_sum import SumModelBuilder
from ai.src.data.process_sum import SumProcessor
from ai.src.metrics.metric_sum import SumMetrics

def train_summarization(config_path: str):
    from ai.src.config import load_config
    cfg = load_config(config_path)

    # 1. Build model
    model, tok = SumModelBuilder.build(
        model_name=cfg["model"]["name"],
        task_type="summarization",
        use_lora=True
    )
    tokenizer = tok

    # 2. Load dataset và GIỚI HẠN SỐ LƯỢNG (Subsampling)
    train_ds = load_from_disk(cfg["data"]["train_path"])
    val_ds = load_from_disk(cfg["data"]["val_path"])

    # --- LOGIC CẮT DATA ---
    if "max_train_samples" in cfg["data"]:
        m_train = cfg["data"]["max_train_samples"]
        if m_train < len(train_ds):
            print(f"[INFO] Cat bot du lieu Train: {len(train_ds)} -> {m_train}")
            train_ds = train_ds.shuffle(seed=42).select(range(m_train))

    if "max_val_samples" in cfg["data"]:
        m_val = cfg["data"]["max_val_samples"]
        if m_val < len(val_ds):
            print(f"[INFO] Cat bot du lieu Val: {len(val_ds)} -> {m_val}")
            val_ds = val_ds.shuffle(seed=42).select(range(m_val))

    # 3. Tokenize
    word_seg = "bartpho-word" in cfg["model"]["name"].lower()
    processor = SumProcessor(
        tokenizer=tokenizer,
        max_input_length=cfg["model"]["max_input_length"],
        max_target_length=cfg["model"]["max_target_length"],
        word_segment=word_seg
    )

    train_tokenized = train_ds.map(processor.process, batched=True, remove_columns=train_ds.column_names)
    val_tokenized = val_ds.map(processor.process, batched=True, remove_columns=val_ds.column_names)

    # 4. Training args
    tcfg = cfg["training"]
    training_args = Seq2SeqTrainingArguments(
        output_dir=tcfg["output_dir"],
        num_train_epochs=tcfg["num_train_epochs"],
        learning_rate=float(tcfg["learning_rate"]),
        per_device_train_batch_size=cfg["data"]["batch_size"],
        per_device_eval_batch_size=cfg["evaluation"]["batch_size"],
        gradient_accumulation_steps=tcfg.get("gradient_accumulation_steps", 1),
        eval_strategy="epoch", # v4.45+ dung eval_strategy
        save_strategy="epoch",
        logging_steps=100,
        bf16=cfg.get("bf16", True), # RTX 3090 nen dung bf16
        load_best_model_at_end=True,
        metric_for_best_model="eval_rougeL",
        predict_with_generate=True,
        generation_max_length=cfg["model"]["max_target_length"],
        report_to="none"
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=val_tokenized,
        processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
        compute_metrics=SumMetrics(tokenizer).compute,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    trainer.train()
    trainer.save_model(os.path.join(tcfg["output_dir"], "best"))
    tokenizer.save_pretrained(os.path.join(tcfg["output_dir"], "best"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    train_summarization(args.config)
