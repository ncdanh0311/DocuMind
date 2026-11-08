"""Held-out, document-disjoint QA benchmark. No synthetic labels or model downloads.

python -m ai.benchmark --dataset PATH --output PATH [--validate-only] [--calibrate]
"""
import argparse
import json
import hashlib
import math
from pathlib import Path
import statistics
import time
from ai.src.metrics.metric_qa import normalize as normalize_answer, text_scores
from ai.src.metrics.rouge import rouge_scores


def validate_dataset(data):
    documents = data.get("documents", [])
    questions = data.get("questions", [])
    by_id = {d["id"]: d for d in documents}
    if len(by_id) != len(documents) or len(documents) < 24:
        raise ValueError("At least 24 unique documents required")
    if len(questions) != 240 or len({q["id"] for q in questions}) != 240:
        raise ValueError("Exactly 240 uniquely identified questions required")
    for document in documents:
        if document["split"] not in ("dev", "test") or not document["text"].strip():
            raise ValueError("Each document needs canonical text and a dev/test split")
    # Duplicate content across splits would leak calibration examples into the test set.
    contents = {}
    for document in documents:
        normalized = normalize_answer(document["text"])
        if normalized in contents and contents[normalized] != document["split"]:
            raise ValueError("Document content overlaps dev and test")
        contents[normalized] = document["split"]
    for split in ("dev", "test"):
        subset = [q for q in questions if q["split"] == split]
        if len(subset) != 120 or sum(not q["answers"] for q in subset) != 40:
            raise ValueError("Each split requires 80 answerable and 40 unanswerable questions")
    for q in questions:
        doc = by_id.get(q["document_id"])
        if doc is None or doc["split"] != q["split"] or not q["question"].strip():
            raise ValueError("Question document must belong to the same split")
        for answer in q["answers"]:
            start, end = answer["start"], answer["end"]
            if not 0 <= start < end <= len(doc["text"]) or doc["text"][start:end] != answer["text"]:
                raise ValueError("Gold answers require exact half-open Unicode character offsets")
    return by_id


def choose_threshold(records, max_false_positive=0.05):
    """Calibrate only on dev; choose highest text F1 under the negative FPR limit."""
    scores = [r["score"] for r in records if r["score"] is not None]
    thresholds = sorted(set(scores + [max(scores, default=0) + 1]))
    negatives = [r for r in records if not r["answers"]]
    if not negatives: raise ValueError("Calibration requires unanswerable questions")
    valid = []
    for threshold in thresholds:
        fp = sum(r["score"] is not None and r["score"] >= threshold for r in negatives) / len(negatives)
        if fp > max_false_positive: continue
        f1 = statistics.mean(text_scores(r["answer"] if r["score"] is not None and r["score"] >= threshold else "", r["answers"] or [""])[1] for r in records)
        valid.append((f1, -fp, threshold))
    return max(valid)[2]


def aggregate(records, threshold):
    positives = [r for r in records if r["answers"]]
    negatives = [r for r in records if not r["answers"]]
    accepted = lambda r: r["score"] is not None and r["score"] >= threshold
    scoring = [text_scores(r["answer"] if accepted(r) else "", r["answers"] or [""]) for r in records]
    times = sorted(r["latency_seconds"] for r in records)
    return {
        "questions": len(records), "threshold": threshold,
        "recall_at_20": statistics.mean(r["recall20"] for r in positives),
        "recall_at_3": statistics.mean(r["recall3"] for r in positives),
        "em": statistics.mean(s[0] for s in scoring), "f1": statistics.mean(s[1] for s in scoring),
        "no_answer_accuracy": statistics.mean(not accepted(r) for r in negatives),
        "false_positive_rate": statistics.mean(accepted(r) for r in negatives),
        "source_accuracy": statistics.mean(accepted(r) and r["source_correct"] for r in positives),
        "latency_p50_seconds": statistics.median(times),
        "latency_p95_seconds": times[max(0, math.ceil(len(times) * .95) - 1)],
    }


def run(data, calibrate=False):
    from ai.runtime.models import runtime
    from ai.runtime.registry import registry, manifest_version
    from ai.services.embedding_service import embedding_service
    from ai.services.reranker_service import reranker_service
    from ai.services.qa_service import qa_service
    from ai.services.summarization_service import summarization_service
    validate_dataset(data)
    for model in ("embedding", "reranker", "phobert_qa", "xlmroberta_qa", "vit5", "bartpho"): registry.bundle(model)
    report = {"protocol": "phase2-v1", "dataset_sha256": hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "models": {}, "qa": {}, "summaries": [], "manual_rubric": {
        "factuality": "1-5: every claim supported by source", "coverage": "1-5: important source points retained",
        "readability": "1-5: coherent Vietnamese", "status": "requires_human_review"}}
    for model in ("embedding", "reranker", "phobert_qa", "xlmroberta_qa", "vit5", "bartpho"):
        report["models"][model] = registry.bundle(model)[0].version
    corpora = {}
    for split in ("dev", "test"):
        chunks = []
        for doc in data["documents"]:
            if doc["split"] != split: continue
            for span in runtime.split(doc["text"], "embedding", overlap=64):
                chunks.append({"chunk_id": str(len(chunks)), "document_id": doc["id"], **span, "content": doc["text"][span["start"]:span["end"]]})
        vectors = []
        for i in range(0, len(chunks), 16): vectors.extend(embedding_service.embed_text([c["content"] for c in chunks[i:i+16]]))
        corpora[split] = chunks, vectors
    for model in ("phobert_qa", "xlmroberta_qa"):
        records = {"dev": [], "test": []}
        for q in data["questions"]:
            started = time.perf_counter()
            chunks, vectors = corpora[q["split"]]
            query = embedding_service.embed_text([q["question"]], is_query=True)[0]
            top20 = sorted(range(len(chunks)), key=lambda i: sum(x*y for x, y in zip(query, vectors[i])), reverse=True)[:20]
            retrieved = [chunks[i] for i in top20]
            ranking = reranker_service.rerank(q["question"], [c["content"] for c in retrieved], top_k=3)
            top3 = [retrieved[r["index"]] for r in ranking]
            result = qa_service.answer(top3, q["question"], model, calibrated=False)
            matched = next((c for c in top3 if c["chunk_id"] == result["chunk_id"]), None)
            def includes_gold(c): return c["document_id"] == q["document_id"] and any(c["start"] <= a["start"] and c["end"] >= a["end"] for a in q["answers"])
            source_correct = bool(matched and matched["document_id"] == q["document_id"] and any(
                matched["start"] + result["start"] == a["start"] and matched["start"] + result["end"] == a["end"] for a in q["answers"]))
            records[q["split"]].append({"id": q["id"], "answer": result["answer"], "answers": [a["text"] for a in q["answers"]],
                "score": result["score"], "source_correct": source_correct, "recall20": any(map(includes_gold, retrieved)),
                "recall3": any(map(includes_gold, top3)), "latency_seconds": time.perf_counter() - started,
                "predicted_document_id": matched["document_id"] if matched else None,
                "predicted_start": matched["start"] + result["start"] if matched else None,
                "predicted_end": matched["start"] + result["end"] if matched else None})
        threshold = choose_threshold(records["dev"])
        report["qa"][model] = {split: aggregate(values, threshold) for split, values in records.items()}
        report["qa"][model]["predictions"] = records
        if calibrate:
            manifest, directory = registry.bundle(model)
            payload = manifest.model_dump(); payload["qa_threshold"] = threshold; payload["version"] = manifest_version(payload)
            temporary = directory / "manifest.tmp"
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(directory / "manifest.json")
            report["qa"][model]["calibrated_version"] = payload["version"]
    for model in ("vit5", "bartpho"):
        for doc in data["documents"]:
            if not doc.get("summary_reference"): continue
            started = time.perf_counter()
            values = [doc["text"]]
            for _ in range(12):
                combined = "\n\n".join(values)
                spans = runtime.split(combined, model)
                values = [summarization_service.summarize(combined[s["start"]:s["end"]], model, max_output_tokens=128)["summary"] for s in spans]
                if len(values) == 1: break
            else: raise ValueError("ERR_SUMMARY_REDUCTION")
            report["summaries"].append({"document_id": doc["id"], "model": model, "summary": values[0],
                **rouge_scores(values[0], doc["summary_reference"]), "latency_seconds": time.perf_counter() - started, "manual_scores": None})
    report["summary_status"] = "requires_human_review" if report["summaries"] else "missing_reference_summaries"
    report["summary_metrics"] = {}
    for model in ("vit5", "bartpho"):
        rows = [row for row in report["summaries"] if row["model"] == model]
        if rows: report["summary_metrics"][model] = {key: statistics.mean(row[key] for row in rows) for key in ("rouge1", "rouge2", "rougeL")}
    import torch
    report["peak_cuda_memory_bytes"] = torch.cuda.max_memory_allocated() if torch.cuda.is_available() else None
    try:
        import resource
        import sys
        report["peak_process_memory_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    except ImportError: pass
    try:
        import psutil
        memory = psutil.Process().memory_info()
        report["process_memory_bytes"] = getattr(memory, "peak_wset", memory.rss)
        if hasattr(memory, "peak_wset"): report["peak_process_memory_bytes"] = memory.peak_wset
    except ImportError: report["process_memory_bytes"] = None
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()
    data = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    validate_dataset(data)
    report = {"status": "dataset_valid", "model_inference_run": False} if args.validate_only else run(data, args.calibrate)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__": main()
