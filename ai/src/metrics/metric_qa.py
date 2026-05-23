import numpy as np
import re
from collections import Counter
from transformers import EvalPrediction


class QAMetrics:

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def compute(eval_pred: EvalPrediction):
        logits = eval_pred.predictions
        labels = eval_pred.label_ids

        start_logits, end_logits = logits
        start_labels, end_labels = labels

        start_preds = np.argmax(start_logits, axis=-1)
        end_preds   = np.argmax(end_logits,   axis=-1)

        exact_list, f1_list = [], []

        for sp, ep, sl, el in zip(start_preds, end_preds,
                                  start_labels, end_labels):
            pred_start = int(sp)
            pred_end   = int(ep)
            gold_start = int(sl)
            gold_end   = int(el)

            if pred_start > pred_end:
                pred_end = pred_start

            em = float(pred_start == gold_start and pred_end == gold_end)
            exact_list.append(em)

            pred_set = set(range(pred_start, pred_end + 1))
            gold_set = set(range(gold_start, gold_end + 1))
            overlap  = len(pred_set & gold_set)

            if overlap == 0:
                f1_list.append(0.0)
                continue

            precision = overlap / len(pred_set)
            recall    = overlap / len(gold_set)
            f1_list.append(2 * precision * recall / (precision + recall))

        return {
            "exact_match": float(np.mean(exact_list)),
            "f1":          float(np.mean(f1_list)),
        }
