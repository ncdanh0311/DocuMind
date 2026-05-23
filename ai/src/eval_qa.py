import os, sys, yaml, argparse
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from src.data.data_loader import DataLoader
from src.data.process_qa import QAProcessor
from src.models.build_qa import QAModelBuilder
from src.metrics.metric_qa import QAMetrics
from transformers import Trainer, TrainingArguments, DefaultDataCollator

def eval_qa(config_path: str):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    run_name = os.path.basename(config_path).replace(".yaml", "")
    best_model_path = os.path.join(cfg["training"]["output_dir"], "best_model")

    model, tokenizer = QAModelBuilder.build(best_model_path, cache_dir=best_model_path)

    dataset = DataLoader.load(cfg["data"]["train_path"].replace("/train", ""))
    processor = QAProcessor(tokenizer, max_length=cfg["model"]["max_length"], doc_stride=cfg["model"]["doc_stride"])
    tokenized_ds = dataset.map(processor.process, batched=True, num_proc=1, remove_columns=dataset["train"].column_names)

    args = TrainingArguments(
        output_dir="/tmp/eval_tmp",
        per_device_eval_batch_size=cfg["evaluation"].get("batch_size", 32),
        bf16=cfg.get("bf16", True),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        data_collator=DefaultDataCollator(),
        compute_metrics=QAMetrics.compute,
    )

    print("\n[TEST] Danh gia lai tap Test sau khi fix metric...")
    test_results = trainer.evaluate(tokenized_ds["validation"], metric_key_prefix="test")
    for k, v in test_results.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    eval_qa(args.config)
