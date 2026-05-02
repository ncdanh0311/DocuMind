import os
import sys
import yaml
import argparse
import torch
from transformers import (
    TrainingArguments, 
    Trainer, 
    DataCollatorWithPadding, 
    EarlyStoppingCallback
)

# Thiet lap ROOT_DIR
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from src.data.data_loader import DataLoader
from src.data.process_qa import QAProcessor
from src.models.build_qa import QAModelBuilder
from src.metrics.metric_qa import QAMetrics
from src.logger import ResearchLogger

def train_qa(config_path):
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    run_name = os.path.basename(config_path).replace(".yaml", "")
    
    # 1. Build Model (Sử dụng use_fast=True trong Builder)
    model, tokenizer = QAModelBuilder.build(cfg['model']['name'])
    
    # 2. Load Data
    dataset = DataLoader.load(cfg['data']['train_path'].replace("/train", ""))
    processor = QAProcessor(tokenizer, cfg['model']['max_length'], cfg['model']['doc_stride'])
    
    print("[INFO] Dang Tokenizing du lieu QA (Sliding Window)...")
    # batched=True + num_proc=1 là công thức chống lỗi batch size
    tokenized_ds = dataset.map(
        processor.process, 
        batched=True, 
        num_proc=1, 
        remove_columns=dataset["train"].column_names 
    )

    # 3. Setup Arguments cho RTX 5060 Ti
    args = TrainingArguments(
        output_dir=cfg['training']['output_dir'],
        num_train_epochs=cfg['training']['num_train_epochs'],
        per_device_train_batch_size=cfg['data']['batch_size'],
        per_device_eval_batch_size=32,
        learning_rate=float(cfg['training']['learning_rate']),
        bf16=True, 
        optim="adamw_torch_fused",
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1", 
        save_total_limit=1,
        remove_unused_columns=True, # Đảm bảo loại bỏ các cột không thuộc signature model
        report_to="none"
    )

    # Dùng DataCollatorWithPadding để dóng hàng các chuỗi có độ dài khác nhau
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized_ds['train'],
        eval_dataset=tokenized_ds['validation'],
        processing_class=tokenizer, 
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=QAMetrics.compute,
        callbacks=[ResearchLogger(os.path.join(ROOT_DIR, "results", "logs", f"{run_name}_history.csv")), 
                   EarlyStoppingCallback(early_stopping_patience=3)]
    )

    print(f"[START] Training QA: {run_name}")
    trainer.train()
    
    # Đánh giá Test cuối cùng
    print("\n[TEST] Dang danh gia tap TEST mu...")
    test_results = trainer.evaluate(tokenized_ds['test'], metric_key_prefix="test")
    
    report_path = os.path.join(ROOT_DIR, "results", "logs", f"{run_name}_results.txt")
    with open(report_path, "a") as f:
        f.write("\n=== KET QUA TEST CUOI CUNG (QA) ===\n")
        for k, v in test_results.items(): f.write(f"{k.upper()}: {v}\n")

    trainer.save_model(os.path.join(cfg['training']['output_dir'], "best_model"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    train_qa(args.config)