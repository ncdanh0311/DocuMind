from pathlib import Path

class DataLoader:
    @staticmethod
    def load(path):
        from datasets import DatasetDict, load_from_disk
        root = Path(path)
        if not root.is_dir(): raise FileNotFoundError(f"Dataset directory does not exist: {root}")
        dataset = load_from_disk(str(root)) if (root / "dataset_dict.json").is_file() else DatasetDict({
            split: load_from_disk(str(root / split)) for split in ("train", "validation", "test")
        })
        if not all(split in dataset for split in ("train", "validation", "test")):
            raise ValueError("Dataset must contain independent train, validation and test splits")
        return dataset
