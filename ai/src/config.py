from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]

def load_config(path):
    """Training paths are relative to ai/, independent of the shell working directory."""
    import yaml
    with Path(path).open(encoding="utf-8") as stream: config = yaml.safe_load(stream)
    for section, keys in (("data", ("train_path", "val_path", "test_path")), ("training", ("output_dir",)), ("model", ("base_path",))):
        for key in keys:
            value = config.get(section, {}).get(key)
            if value and not Path(value).is_absolute(): config[section][key] = (AI_ROOT / value).as_posix()
    return config
