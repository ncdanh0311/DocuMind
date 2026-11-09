"""Import an existing trained checkpoint; never substitute an untrained base QA head.
python -m ai.import_model --model phobert_qa --source PATH [--base-source PATH]
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid
from ai.runtime.registry import Manifest, MODEL_TASKS, manifest_version

def import_bundle(model_id, source, destination, base_source=None, qa_threshold=None):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir(): raise ValueError("Checkpoint directory does not exist")
    if destination.exists(): raise ValueError("Destination already exists; choose a new bundle root")
    if destination.is_relative_to(source) or source.is_relative_to(destination): raise ValueError("Source and destination must be separate")
    adapter = (source / "adapter_config.json").is_file()
    if adapter and base_source is None: raise ValueError("LoRA checkpoint requires --base-source pointing to the exact local base model")
    if not (source / "tokenizer_config.json").is_file(): raise ValueError("Checkpoint must include its trained tokenizer")
    if not any(source.glob("*.safetensors")) and not any(source.glob("*.bin")): raise ValueError("No checkpoint weights found")
    from transformers import AutoTokenizer, AutoConfig
    task = MODEL_TASKS[model_id]
    tokenizer = AutoTokenizer.from_pretrained(source, local_files_only=True, use_fast=task in ("qa", "embedding", "reranker"))
    if task == "qa" and not tokenizer.is_fast: raise ValueError("QA requires a matching fast tokenizer with offset mappings")
    config = AutoConfig.from_pretrained(base_source if adapter else source, local_files_only=True)
    position_limit = getattr(config, "max_position_embeddings", 512)
    if getattr(config, "model_type", "") in ("roberta", "xlm-roberta"): position_limit -= 2
    tokenizer_limit = tokenizer.model_max_length
    max_input = min(position_limit, tokenizer_limit if tokenizer_limit < 100000 else 512, 512)
    defaults = {"phobert_qa": "phobert", "bartpho": "bartpho"}
    manifest = Manifest(id=model_id, task=task, version="pending", files={"pending": "pending"},
        base_path="base" if adapter else None, base_revision=str(getattr(config, "_commit_hash", None) or "local-checksummed"),
        preprocessing=defaults.get(model_id, "raw"), max_input_tokens=max_input, qa_threshold=qa_threshold)
    temporary = destination.parent / (".import-" + str(uuid.uuid4()))
    temporary.mkdir(parents=True)
    try:
        shutil.copytree(source, temporary / "model")
        if adapter: shutil.copytree(Path(base_source).resolve(), temporary / "base")
        files = {}
        for path in sorted(temporary.rglob("*")):
            if not path.is_file(): continue
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                while block := stream.read(1024 * 1024): digest.update(block)
            files[path.relative_to(temporary).as_posix()] = digest.hexdigest()
        payload = manifest.model_dump(); payload["files"] = files; payload["version"] = manifest_version(payload)
        (temporary / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        # Load exact offline weights and run a real forward pass before publishing availability.
        from ai.runtime.registry import ModelRegistry
        from ai.runtime.models import ModelRuntime
        validation_root = temporary.parent / (".validate-" + str(uuid.uuid4()))
        validation_root.mkdir()
        temporary.rename(validation_root / model_id)
        try:
            runtime = ModelRuntime(ModelRegistry(validation_root))
            with runtime.lock:
                _, tok, model, device = runtime.load(model_id)
                import torch
                example = tok("Kiểm tra mô hình.", return_tensors="pt").to(device)
                with torch.inference_mode():
                    if task == "summarization": model.generate(**example, max_new_tokens=2)
                    else:
                        output = model(**example)
                        if task == "embedding" and output.last_hidden_state.shape[-1] != 384: raise ValueError("ERR_EMBEDDING_SHAPE")
                        if task == "reranker" and output.logits.shape[-1] != 1: raise ValueError("ERR_RERANK_SHAPE")
            (validation_root / model_id).rename(destination)
        finally:
            shutil.rmtree(validation_root)
        return payload
    finally:
        if temporary.exists(): shutil.rmtree(temporary)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODEL_TASKS, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--base-source")
    parser.add_argument("--root", default="ai/artifacts")
    parser.add_argument("--qa-threshold", type=float)
    args = parser.parse_args()
    manifest = import_bundle(args.model, args.source, Path(args.root) / args.model, args.base_source, args.qa_threshold)
    print(json.dumps({"id": manifest["id"], "version": manifest["version"], "calibrated": manifest["qa_threshold"] is not None}))

if __name__ == "__main__": main()
