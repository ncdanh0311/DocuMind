import numpy as np

class QAMetrics:
    @staticmethod
    def compute(eval_pred):
        logits, labels = eval_pred
        start_logits, end_logits = logits
        start_labels, end_labels = labels
        
        start_preds = np.argmax(start_logits, axis=-1)
        end_preds = np.argmax(end_logits, axis=-1)
        
        exact_match = np.mean(
            (start_preds == start_labels) & (end_preds == end_labels)
        )
        f1 = (
            np.mean(start_preds == start_labels) + 
            np.mean(end_preds == end_labels)
        ) / 2
        
        return {
            "exact_match": float(exact_match),
            "f1": float(f1)
        }