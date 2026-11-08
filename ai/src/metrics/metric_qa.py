"""Text EM/F1, aggregated across overflow windows and multiple gold answers."""
from collections import Counter
import unicodedata

def normalize(text):
    text = unicodedata.normalize("NFC", text).casefold()
    return " ".join("".join(" " if unicodedata.category(c).startswith("P") else c for c in text).split())

def text_scores(prediction, golds):
    scores = []
    for gold in golds or [""]:
        p, g = normalize(prediction), normalize(gold)
        left, right = p.split(), g.split()
        if not left or not right: f1 = float(left == right)
        else:
            overlap = sum((Counter(left) & Counter(right)).values())
            f1 = 2 * overlap / (len(left) + len(right))
        scores.append((float(p == g), f1))
    return max((em for em, _ in scores), default=0), max((f1 for _, f1 in scores), default=0)

class QAMetrics:
    @staticmethod
    def for_dataset(features, examples, threshold=0.0):
        feature_rows = list(features)
        example_rows = list(examples)
        def compute(eval_pred):
            start_logits, end_logits = eval_pred.predictions[:2]
            predictions = {}
            for feature, starts, ends in zip(feature_rows, start_logits, end_logits):
                offsets = feature["offset_mapping"]
                valid = [i for i, span in enumerate(offsets) if span is not None]
                firsts = sorted(valid, key=lambda i: float(starts[i]), reverse=True)[:20]
                lasts = sorted(valid, key=lambda i: float(ends[i]), reverse=True)[:20]
                example_id = str(feature["example_id"])
                for first in firsts:
                    for last in lasts:
                        if first > last or last - first >= 100: continue
                        score = float(starts[first] + ends[last] - starts[0] - ends[0])
                        candidate = (score, offsets[first][0], offsets[last][1])
                        if example_id not in predictions or score > predictions[example_id][0]: predictions[example_id] = candidate
            scores = []
            for example in example_rows:
                candidate = predictions.get(str(example["id"]))
                answer = example["context"][candidate[1]:candidate[2]] if candidate and candidate[0] >= threshold else ""
                scores.append(text_scores(answer, example["answers"]["text"]))
            return {"exact_match": 100 * sum(s[0] for s in scores) / len(scores), "f1": 100 * sum(s[1] for s in scores) / len(scores)}
        return compute
