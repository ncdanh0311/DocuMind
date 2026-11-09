"""Unicode word ROUGE for Vietnamese; no English stemming or ASCII-only tokenization."""
from collections import Counter
from ai.src.metrics.metric_qa import normalize

def rouge_scores(prediction, reference):
    a, b = normalize(prediction).split(), normalize(reference).split()
    def f1(hit, predicted, gold): return 2 * hit / (predicted + gold) if predicted + gold else 1.0
    result = {}
    for n in (1, 2):
        x, y = Counter(tuple(a[i:i+n]) for i in range(len(a)-n+1)), Counter(tuple(b[i:i+n]) for i in range(len(b)-n+1))
        result[f"rouge{n}"] = f1(sum((x & y).values()), sum(x.values()), sum(y.values()))
    previous = [0] * (len(b) + 1)
    for word in a:
        current = [0]
        for j, other in enumerate(b): current.append(previous[j] + 1 if word == other else max(previous[j + 1], current[-1]))
        previous = current
    result["rougeL"] = f1(previous[-1], len(a), len(b))
    return result
