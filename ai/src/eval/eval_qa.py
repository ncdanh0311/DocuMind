import os
import sys
import yaml
import json
import time
import argparse
from transformers import Trainer, DefaultDataCollator

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from src.data.data_loader import DataLoader
from src.data.process_qa import QAProcessor
from src.models.build_qa import QAModelBuilder
from src.metrics.metric_qa import QAMetrics

def evaluate_qa(config_path):
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
        
    run_name = os.path.basename(config_path).replace(".yaml", "")
    best_model_path = os.path.join(cfg['training']['output_dir'], "best_model")
    
    print(f"[INFO] Bat dau danh gia tap Test cho: {run_name}")
    
    if not os.path.exists(best_model_path):
        raise FileNotFoundError(f"Khong tim thay model da train tai {best_model_path}")

    model, tokenizer = QAModelBuilder.build(best_model_path)
    
    dataset = DataLoader.load(cfg['data']['train_path'].replace("/train", ""))
    processor = QAProcessor(tokenizer, cfg['model']['max_length'], cfg['model']['doc_stride'])
    
    print("[INFO] Dang ma hoa tap Test...")
    test_ds = dataset['test'].map(processor.process, batched=True, remove_columns=dataset['test'].column_names)

    trainer = Trainer(
        model=model,
        eval_dataset=test_ds,
        tokenizer=tokenizer,
        data_collator=DefaultDataCollator(),
        compute_metrics=QAMetrics.compute
    )

    print("[INFO] Dang thuc thi Inference tren tap Test...")
    start_time = time.time()
    results = trainer.evaluate()
    inference_time = time.time() - start_time
    
    results["total_inference_time_sec"] = round(inference_time, 2)
    results["samples_per_second"] = round(len(test_ds) / inference_time, 2)

    report_path = os.path.join(ROOT_DIR, "results", "logs", f"{run_name}_test_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print("[INFO] KET QUA TEST:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print(f"[INFO] Da luu bao cao vao {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    evaluate_qa(args.config)