import os
import sys
import yaml
import argparse
import torch
import time
import glob
from transformers import (
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer, 
    DataCollatorForSeq2Seq, 
    EarlyStoppingCallback
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.data.data_loader import DataLoader
from src.data.process_sum import SumProcessor
from src.models.build_sum import SumModelBuilder
from src.metrics.metric_sum import SumMetrics
from src.logger import ResearchLogger

def train_summarization(config_path):
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    run_name = os.path.basename(config_path).replace(".yaml", "")
    
    # 1. Build Model & Tokenizer (LoRA=True)
    model, tokenizer = SumModelBuilder.build(cfg['model']['name'], task_type="summarization", use_lora=True)

    # 2. Load & Sample Data
    dataset = DataLoader.load(cfg['data']['train_path'].replace("/train", ""))
    
    # --- CẮT DỮ LIỆU THEO CONFIG (Val 500 mẫu để chạy cho nhanh) ---
    for split in ["train", "validation", "test"]:
        max_key = f"max_{split}_samples"
        max_samples = cfg['data'].get(max_key, 20000 if split == "train" else 500)
        if len(dataset[split]) > max_samples:
            dataset[split] = dataset[split].shuffle(seed=42).select(range(max_samples))

    # 3. Tokenize
    processor = SumProcessor(tokenizer, cfg['model']['max_input_length'], cfg['model']['max_target_length'])
    print(f"[INFO] Tokenizing Data: Train({len(dataset['train'])}) | Val({len(dataset['validation'])}) | Test({len(dataset['test'])})")
    tokenized_ds = dataset.map(processor.process, batched=True, num_proc=16, remove_columns=dataset["train"].column_names)

    # 4. Training Arguments
    args = Seq2SeqTrainingArguments(
        output_dir=cfg['training']['output_dir'],
        num_train_epochs=cfg['training']['num_train_epochs'],
        per_device_train_batch_size=cfg['data']['batch_size'],
        per_device_eval_batch_size=8,
        learning_rate=float(cfg['training']['learning_rate']),
        bf16=True,
        optim="adamw_torch_fused",
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        save_total_limit=1,
        predict_with_generate=True,
        dataloader_num_workers=16,
        remove_unused_columns=True,
        report_to="none"
    )

    log_path = os.path.join(ROOT_DIR, "results", "logs", f"{run_name}_history.csv")
    logger_cb = ResearchLogger(log_path)

    # 5. Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=tokenized_ds['train'],
        eval_dataset=tokenized_ds['validation'],
        processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
        compute_metrics=SumMetrics(tokenizer).compute, # Nhớ file này phải có lệnh .replace("_", " ")
        callbacks=[logger_cb, EarlyStoppingCallback(early_stopping_patience=cfg['training']['early_stopping_patience'])]
    )

    # --- 6. AUTO RESUME ---
    checkpoint = None
    if os.path.isdir(args.output_dir):
        checkpoints = glob.glob(os.path.join(args.output_dir, "checkpoint-*"))
        if checkpoints:
            checkpoint = max(checkpoints, key=os.path.getmtime)
            print(f"\n[RESUME] Chạy tiếp từ: {checkpoint}")

    # 7. Chạy Huấn Luyện
    trainer.train(resume_from_checkpoint=checkpoint)
    
    # --- 8. ĐÁNH GIÁ CUỐI CÙNG TRÊN 2000 MẪU TEST (QUAN TRỌNG) ---
    print(f"\n[FINAL TEST] Đang đánh giá trên {len(tokenized_ds['test'])} mẫu Test mù...")
    # Ép cấu hình max_length 256 cho bước Test
    test_results = trainer.evaluate(tokenized_ds['test'], metric_key_prefix="test")
    
    # Ghi kết quả vào file kết quả cuối cùng
    with open(logger_cb.txt_path, "a", encoding="utf-8") as f:
        f.write("\n" + "="*40 + "\n")
        f.write("KET QUA NGHIEN CUU TREN TAP TEST (2000 mẫu)\n")
        for k, v in test_results.items():
            f.write(f"  {k.upper()}: {v}\n")
            
    trainer.save_model(os.path.join(cfg['training']['output_dir'], "best_model"))
    print(f"[OK] Đã hoàn thành và xuất báo cáo tại: {logger_cb.txt_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    train_summarization(args.config)