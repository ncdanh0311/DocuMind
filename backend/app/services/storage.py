from pathlib import Path
from backend.app.core.config import settings

def storage_root() -> Path:
    root = Path(settings.UPLOAD_DIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root

def source_path(key: str) -> Path:
    root = storage_root()
    path = (root / key).resolve()
    if not path.is_relative_to(root): raise ValueError("ERR_INVALID_STORAGE_KEY")
    return path
