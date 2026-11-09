"""The same Unicode ROUGE definitions are used for training, test and benchmark."""
import numpy as np
from ai.src.metrics.rouge import rouge_scores

class SumMetrics:
    def __init__(self, tokenizer): self.tokenizer = tokenizer

    def compute(self, eval_pred):
        predictions, labels = eval_pred
        if isinstance(predictions, tuple): predictions = predictions[0]
        def array(value):
            if hasattr(value, "detach"): value = value.detach().cpu().numpy()
            return np.asarray(value)
        predictions, labels = array(predictions), array(labels)
        predictions = np.where(predictions >= 0, predictions, self.tokenizer.pad_token_id)
        labels = np.where(labels >= 0, labels, self.tokenizer.pad_token_id)
        decoded = self.tokenizer.batch_decode(predictions, skip_special_tokens=True)
        references = self.tokenizer.batch_decode(labels, skip_special_tokens=True)
        scores = [rouge_scores(p.replace("_", " "), r.replace("_", " ")) for p, r in zip(decoded, references)]
        return {key: round(100 * sum(s[key] for s in scores) / len(scores), 4) for key in ("rouge1", "rouge2", "rougeL")} if scores else {}
