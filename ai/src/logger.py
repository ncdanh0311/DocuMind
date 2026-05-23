import time
import pandas as pd
import os
from transformers import TrainerCallback


class ResearchLogger(TrainerCallback):
    def __init__(self, log_path, metric_for_best="eval_loss", greater_is_better=False):
        self.log_path = log_path
        self.history = []
        self.start_time = time.time()
        self.epoch_start_time = None
        self.best_metrics = {}
        self.metric_for_best = metric_for_best
        self.greater_is_better = greater_is_better
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.txt_path = self.log_path.replace("_history.csv", "_results.txt")

        # Buffer tích lũy log trong epoch
        self._epoch_buffer = {}

    def on_epoch_begin(self, args, state, control, **kwargs):
        self.epoch_start_time = time.time()
        self._epoch_buffer = {}

    def on_log(self, args, state, control, logs=None, **kwargs):
        """Gọi mỗi lần Trainer log — tích lũy cả train lẫn eval."""
        if logs:
            self._epoch_buffer.update(logs)

        # Chỉ print/save khi đã có đủ cả train loss lẫn eval loss
        has_train = "loss" in self._epoch_buffer
        has_eval  = "eval_loss" in self._epoch_buffer
        if not (has_train and has_eval):
            return

        epoch_duration = time.time() - self.epoch_start_time
        total_duration = time.time() - self.start_time
        current_epoch  = round(state.epoch)

        train_loss = round(self._epoch_buffer["loss"], 4)
        val_loss   = round(self._epoch_buffer["eval_loss"], 6)

        entry = {
            "epoch":          current_epoch,
            "train_loss":     train_loss,
            "val_loss":       val_loss,
            "epoch_time_min": round(epoch_duration / 60, 2),
            "total_time_min": round(total_duration / 60, 2),
        }

        for k, v in self._epoch_buffer.items():
            if k.startswith("eval_") and k not in (
                "eval_loss", "eval_runtime",
                "eval_samples_per_second", "eval_steps_per_second",
            ):
                entry[k.replace("eval_", "")] = (
                    round(v, 4) if isinstance(v, float) else v
                )

        current_val = self._epoch_buffer.get(self.metric_for_best)
        if current_val is not None:
            best_so_far = self.best_metrics.get("_best_val")
            is_better = (
                best_so_far is None
                or (self.greater_is_better     and current_val > best_so_far)
                or (not self.greater_is_better and current_val < best_so_far)
            )
            if is_better:
                self.best_metrics = entry.copy()
                self.best_metrics["_best_val"] = current_val

        self.history.append(entry)
        pd.DataFrame(self.history).to_csv(self.log_path, index=False)
        self._save_txt()

        print(f"\n--- KET QUA EPOCH {current_epoch} ---")
        print(
            f"Train Loss: {train_loss} | "
            f"Val Loss: {val_loss} | "
            f"Time: {entry['epoch_time_min']}m"
        )

        # Reset buffer sau khi đã log xong epoch
        self._epoch_buffer = {}

    def on_epoch_end(self, args, state, control, **kwargs):
        pass  # logic đã chuyển sang on_log

    def _save_txt(self):
        with open(self.txt_path, "w", encoding="utf-8") as f:
            f.write("=== LICH SU HUAN LUYEN CHI TIET ===\n")
            for e in self.history:
                f.write(
                    f"EPOCH {e['epoch']}: "
                    f"TrainLoss={e['train_loss']}, "
                    f"ValLoss={e['val_loss']}, "
                    f"Time={e['epoch_time_min']}m\n"
                )
            if self.best_metrics:
                f.write("\n=== KET QUA TOT NHAT (BEST MODEL) ===\n")
                for k, v in self.best_metrics.items():
                    if not k.startswith("_"):
                        f.write(f"{k.upper()}: {v}\n")