from pathlib import Path
import os
from transformers import PreTrainedTokenizerFast, AutoModelForQuestionAnswering
from huggingface_hub import snapshot_download


class QAModelBuilder:

    @staticmethod
    def build(model_name: str, cache_dir: str = str(Path(__file__).resolve().parents[2] / "hf_cache")):
        print(f"[INFO] Nap mo hinh QA: {model_name}")

        # Local path → load trực tiếp, không qua snapshot_download
        if os.path.isdir(model_name):
            snapshot_path = model_name
        else:
            snapshot_path = snapshot_download(
                model_name,
                cache_dir=cache_dir,
                local_files_only=True,
            )
        print(f"[INFO] Snapshot: {snapshot_path}")

        tokenizer = PreTrainedTokenizerFast.from_pretrained(snapshot_path)
        tokenizer.bos_token   = "<s>"
        tokenizer.eos_token   = "</s>"
        tokenizer.unk_token   = "<unk>"
        tokenizer.pad_token   = "<pad>"
        tokenizer.cls_token   = "<s>"
        tokenizer.sep_token   = "</s>"
        tokenizer.mask_token  = "<mask>"

        assert tokenizer.is_fast, "[ERROR] Vẫn không phải fast tokenizer"
        print(f"[INFO] Tokenizer: {type(tokenizer).__name__} (is_fast={tokenizer.is_fast})")

        model = AutoModelForQuestionAnswering.from_pretrained(snapshot_path)
        if model.get_input_embeddings().num_embeddings != len(tokenizer):
            raise ValueError("Tokenizer vocabulary does not match checkpoint embeddings")
        maximum = getattr(model.config, "max_position_embeddings", 512)
        if model.config.model_type in ("roberta", "xlm-roberta"): maximum -= 2
        tokenizer.model_max_length = maximum

        return model, tokenizer
