from ai.runtime.models import runtime

class RerankerService:
    def rerank(self, question, passages, top_k=3):
        with runtime.lock:
            manifest, tokenizer, model, device = runtime.load("reranker")
            import torch
            inputs = tokenizer([[question, text] for text in passages], padding=True, truncation="only_second", max_length=manifest.max_input_tokens, return_tensors="pt").to(device)
            with torch.inference_mode(): scores = model(**inputs).logits.flatten().float().cpu().tolist()
            if len(scores) != len(passages): raise ValueError("ERR_RERANK_SHAPE")
            return sorted([{"index": i, "score": score} for i, score in enumerate(scores)], key=lambda row: row["score"], reverse=True)[:top_k]

reranker_service = RerankerService()
