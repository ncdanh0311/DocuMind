"""Extractive QA returns offsets into the original passage, never guessed sources."""
from ai.runtime.models import runtime
from ai.runtime.text import segmented_alignment

class QAService:
    def answer(self, passages, question, model_type="phobert_qa", calibrated=True):
        import torch
        with runtime.lock:
            manifest, tokenizer, model, device = runtime.load(model_type, calibrated)
            if manifest.preprocessing == "phobert":
                from pyvi import ViTokenizer
                segmented_question = ViTokenizer.tokenize(question)
            else: segmented_question = question
            if len(tokenizer.encode(segmented_question)) >= manifest.max_input_tokens - 8:
                raise ValueError("ERR_QUESTION_TOO_LONG")
            candidates = []
            for passage in passages:
                raw = passage["content"]
                if manifest.preprocessing == "phobert":
                    from pyvi import ViTokenizer
                    context = ViTokenizer.tokenize(raw)
                    mapping = segmented_alignment(raw, context)
                else:
                    context, mapping = raw, [(i, i + 1) for i in range(len(raw))]
                encoded = tokenizer(segmented_question, context, truncation="only_second", max_length=manifest.max_input_tokens,
                    stride=min(64, max(0, (manifest.max_input_tokens - len(tokenizer.encode(segmented_question)) - 8) // 2)),
                    return_overflowing_tokens=True, return_offsets_mapping=True, padding=True, return_tensors="pt")
                offsets = encoded.pop("offset_mapping").tolist()
                encoded.pop("overflow_to_sample_mapping", None)
                for window in range(encoded.input_ids.shape[0]):
                    inputs = {key: value[window:window + 1].to(device) for key, value in encoded.items()}
                    with torch.inference_mode(): output = model(**inputs)
                    starts, ends = output.start_logits[0].float().cpu(), output.end_logits[0].float().cpu()
                    valid = [i for i, sequence in enumerate(encoded.sequence_ids(window)) if sequence == 1 and offsets[window][i][1] > offsets[window][i][0]]
                    if not valid: continue
                    top_starts = sorted(valid, key=lambda i: float(starts[i]), reverse=True)[:20]
                    top_ends = sorted(valid, key=lambda i: float(ends[i]), reverse=True)[:20]
                    null_score = float(starts[0] + ends[0])
                    for first in top_starts:
                        for last in top_ends:
                            if first > last or last - first >= 100: continue
                            left, right = offsets[window][first][0], offsets[window][last][1]
                            if not 0 <= left < right <= len(mapping): continue
                            start, end = mapping[left][0], mapping[right - 1][1]
                            if start >= end or not raw[start:end].strip(): continue
                            candidates.append({"chunk_id": passage["chunk_id"], "start": start, "end": end,
                                "answer": raw[start:end], "score": float(starts[first] + ends[last]) - null_score})
            best = max(candidates, key=lambda item: item["score"]) if candidates else None
            accepted = best is not None and (not calibrated or (manifest.qa_threshold is not None and best["score"] >= manifest.qa_threshold))
            return {"status": "answered" if accepted else "no_answer", "answer": best["answer"] if accepted else "",
                "chunk_id": best["chunk_id"] if accepted else None, "start": best["start"] if accepted else None,
                "end": best["end"] if accepted else None, "score": best["score"] if best else None, "model_version": manifest.version}

qa_service = QAService()
