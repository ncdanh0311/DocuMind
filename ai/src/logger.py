import time
import pandas as pd
import os
from transformers import TrainerCallback

class ResearchLogger(TrainerCallback):
    def __init__(self, log_path):
        self.log_path = log_path
        self.history = []
        self.start_time = time.time()
        self.epoch_start_time = None
        self.best_metrics = {}
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.txt_path = self.log_path.replace("_history.csv", "_results.txt")

    def on_epoch_begin(self, args, state, control, **kwargs):
        self.epoch_start_time = time.time()

    def on_epoch_end(self, args, state, control, **kwargs):
        epoch_duration = time.time() - self.epoch_start_time
        total_duration = time.time() - self.start_time
        
        train_loss = "N/A"
        eval_metrics = {}
        
        for log in reversed(state.log_history):
            if "loss" in log and train_loss == "N/A":
                train_loss = round(log["loss"], 4)
            if "eval_loss" in log and not eval_metrics:
                eval_metrics = log
            if train_loss != "N/A" and eval_metrics:
                break

        entry = {
            "epoch": int(state.epoch),
            "train_loss": train_loss,
            "val_loss": eval_metrics.get("eval_loss", "N/A"),
            "epoch_time_min": round(epoch_duration / 60, 2),
            "total_time_min": round(total_duration / 60, 2)
        }
        
        for k, v in eval_metrics.items():
            if k.startswith("eval_") and k not in ["eval_loss", "eval_runtime", "eval_samples_per_second", "eval_steps_per_second"]:
                entry[k.replace("eval_", "")] = round(v, 4) if isinstance(v, float) else v
                
        if eval_metrics.get("eval_loss") is not None:
            if not self.best_metrics or eval_metrics["eval_loss"] < self.best_metrics.get("val_loss", 999):
                self.best_metrics = entry.copy()

        self.history.append(entry)
        pd.DataFrame(self.history).to_csv(self.log_path, index=False)
        self._save_txt(args)

        print(f"\n--- KET QUA EPOCH {entry['epoch']} ---")
        print(f"Train Loss: {train_loss} | Val Loss: {entry['val_loss']} | Time: {entry['epoch_time_min']}m")

    def _save_txt(self, args):
        with open(self.txt_path, "w", encoding="utf-8") as f:
            f.write("=== LICH SU HUAN LUYEN CHI TIET ===\n")
            for e in self.history:
                f.write(f"EPOCH {e['epoch']}: TrainLoss={e['train_loss']}, ValLoss={e['val_loss']}, Time={e['epoch_time_min']}m\n")
            if self.best_metrics:
                f.write("\n=== KET QUA TOT NHAT (BEST MODEL) ===\n")
                for k, v in self.best_metrics.items():
                    f.write(f"{k.upper()}: {v}\n")