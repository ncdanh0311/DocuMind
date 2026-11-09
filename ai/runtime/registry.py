"""Offline, checksummed model bundles. Availability never triggers a download."""
import hashlib
import json
import os
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

MODEL_TASKS = {"phobert_qa": "qa", "xlmroberta_qa": "qa", "vit5": "summarization", "bartpho": "summarization", "embedding": "embedding", "reranker": "reranker"}

class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str
    task: str
    version: str
    files: dict[str, str]
    model_path: str = "model"
    base_path: str | None = None
    base_revision: str | None = None
    preprocessing: str = "raw"
    max_input_tokens: int = Field(ge=16, le=8192)
    max_output_tokens: int = Field(default=128, ge=1, le=512)
    qa_threshold: float | None = None
    generation: dict = Field(default_factory=lambda: {"num_beams": 4, "length_penalty": 1.2, "no_repeat_ngram_size": 3, "do_sample": False})

def manifest_version(payload: dict) -> str:
    return hashlib.sha256(json.dumps({k: v for k, v in payload.items() if k != "version"}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class ModelRegistry:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or os.environ.get("AI_MODEL_ROOT", Path(__file__).resolve().parents[1] / "artifacts")).resolve()
        self._verified = {}

    def bundle(self, model_id: str, require_calibration: bool = False) -> tuple[Manifest, Path]:
        if model_id not in MODEL_TASKS: raise ValueError("ERR_MODEL_ID")
        directory = (self.root / model_id).resolve()
        if not directory.is_relative_to(self.root): raise ValueError("ERR_MODEL_PATH")
        try:
            manifest_file = directory / "manifest.json"
            manifest = Manifest.model_validate_json(manifest_file.read_text(encoding="utf-8"))
            if manifest.version != manifest_version(manifest.model_dump()): raise ValueError("ERR_MODEL_VERSION")
            if manifest.id != model_id or manifest.task != MODEL_TASKS[model_id] or not manifest.files:
                raise ValueError("ERR_MODEL_MANIFEST")
            actual_files = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file() and p != manifest_file}
            if actual_files != set(manifest.files): raise ValueError("ERR_MODEL_UNTRACKED_FILE")
            stamps = []
            for relative, checksum in sorted(manifest.files.items()):
                path = (directory / relative).resolve()
                if not path.is_relative_to(directory) or not path.is_file(): raise ValueError("ERR_MODEL_FILE")
                stamps.append((relative, path.stat().st_size, path.stat().st_mtime_ns, checksum))
            fingerprint = (manifest.version, tuple(stamps))
            if self._verified.get(model_id) != fingerprint:
                for relative, checksum in manifest.files.items():
                    digest = hashlib.sha256()
                    with (directory / relative).open("rb") as stream:
                        while block := stream.read(1024 * 1024): digest.update(block)
                    if digest.hexdigest() != checksum: raise ValueError("ERR_MODEL_CHECKSUM")
                self._verified[model_id] = fingerprint
            for relative in (manifest.model_path, manifest.base_path):
                if relative and (not (directory / relative).resolve().is_relative_to(directory) or not (directory / relative).is_dir()):
                    raise ValueError("ERR_MODEL_PATH")
            if require_calibration and manifest.task == "qa" and manifest.qa_threshold is None:
                raise ValueError("ERR_MODEL_NOT_CALIBRATED")
            return manifest, directory
        except (OSError, ValueError, TypeError) as exc:
            code = str(exc) if str(exc).startswith("ERR_") else "ERR_MODEL_UNAVAILABLE"
            raise FileNotFoundError(code) from None

    def capabilities(self) -> dict:
        models = []
        for model_id, task in MODEL_TASKS.items():
            try:
                manifest, _ = self.bundle(model_id)
                ready = task != "qa" or manifest.qa_threshold is not None
                models.append({"id": model_id, "task": task, "ready": ready, "version": manifest.version,
                    "max_input_tokens": manifest.max_input_tokens, "calibrated": manifest.qa_threshold is not None if task == "qa" else None,
                    "error_code": None if ready else "ERR_MODEL_NOT_CALIBRATED"})
            except FileNotFoundError as exc:
                models.append({"id": model_id, "task": task, "ready": False, "version": None, "error_code": str(exc)})
        return {"models": models}

registry = ModelRegistry()
