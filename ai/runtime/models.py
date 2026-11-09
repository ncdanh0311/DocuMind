import threading
from ai.runtime.registry import registry
from ai.runtime.text import split_to_budget

class ModelRuntime:
    def __init__(self, model_registry=registry):
        self.registry = model_registry
        self.lock = threading.RLock()
        self.loaded = {}

    def load(self, model_id, calibrated=False):
        manifest, directory = self.registry.bundle(model_id, calibrated)
        import torch
        from transformers import AutoTokenizer, AutoModel, AutoModelForQuestionAnswering, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
        cached = self.loaded.get(manifest.task)
        if cached and cached[0].id == model_id and cached[0].version == manifest.version: return cached
        # One loaded model per task; swapping QA/summarizers does not retain both copies.
        self.loaded.pop(manifest.task, None)
        path = directory / manifest.model_path
        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, use_fast=manifest.task in ("qa", "embedding", "reranker"))
        if manifest.task == "qa" and not tokenizer.is_fast: raise ValueError("ERR_FAST_TOKENIZER_REQUIRED")
        model_class = {"qa": AutoModelForQuestionAnswering, "summarization": AutoModelForSeq2SeqLM,
                       "embedding": AutoModel, "reranker": AutoModelForSequenceClassification}[manifest.task]
        if manifest.base_path:
            from peft import PeftModel
            base = model_class.from_pretrained(directory / manifest.base_path, local_files_only=True)
            model = PeftModel.from_pretrained(base, path, local_files_only=True).merge_and_unload()
        else:
            model, loading = model_class.from_pretrained(path, local_files_only=True, output_loading_info=True)
            # Transformers otherwise creates a random QA/classification head for base checkpoints.
            if manifest.task in ("qa", "reranker") and (loading.get("missing_keys") or loading.get("mismatched_keys")):
                raise ValueError("ERR_UNTRAINED_MODEL_HEAD")
        if model.get_input_embeddings().num_embeddings != len(tokenizer):
            raise ValueError("ERR_TOKENIZER_MISMATCH")
        if manifest.task == "qa" and manifest.base_path:
            from peft import PeftConfig
            adapter = PeftConfig.from_pretrained(path, local_files_only=True)
            if not any("qa_outputs" in name for name in (adapter.modules_to_save or [])):
                raise ValueError("ERR_UNTRAINED_MODEL_HEAD")
        device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        model.eval(); model.to(device)
        loaded = (manifest, tokenizer, model, device)
        self.loaded[manifest.task] = loaded
        return loaded

    def preprocess(self, manifest, text):
        if manifest.preprocessing in ("phobert", "bartpho"):
            from pyvi import ViTokenizer
            text = ViTokenizer.tokenize(text)
        if manifest.task == "summarization": return "summarize: " + text
        if manifest.task == "embedding": return "passage: " + text
        return text

    def split(self, text, model_id, overlap=0):
        with self.lock:
            manifest, tokenizer, _, _ = self.load(model_id)
            return split_to_budget(text, lambda value: len(tokenizer.encode(self.preprocess(manifest, value), add_special_tokens=True)), manifest.max_input_tokens, overlap)

runtime = ModelRuntime()
