#!/usr/bin/env python3
import argparse
import yaml
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
from evaluate import load as load_metric

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.build_sum import SumModelBuilder
from src.data.process_sum import SumProcessor

rouge = load_metric("rouge")

def compute_metrics(eval_preds):
    preds, labels = eval_preds
    labels[labels == -100] = 0
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    # Clean "_" cho BARTpho trước khi tính ROUGE
    decoded_preds = [t.replace("_", " ") for t in decoded_preds]
    decoded_labels = [t.replace("_", " ") for t in decoded_labels]

    result = rouge.compute(predictions=decoded_preds, references=decoded_labels, use_stemmer=True)
    return {k: round(v * 100, 4) for k, v in result.items()}

def train_summarization(config_path: str):
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    # 1. Build model
    model, tok = SumModelBuilder.build(
        model_name=cfg["model"]["name"],
        task_type="summarization",
        use_lora=True
    )
    global tokenizer
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
        processing_class=None,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    trainer.train()
    trainer.save_model(os.path.join(tcfg["output_dir"], "best"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    train_summarization(args.config)