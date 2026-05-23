import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    GenerationConfig,
)
from peft import LoraConfig, get_peft_model


class SumModelBuilder:
    @staticmethod
    def build(model_name, task_type="summarization", use_lora=True, cache_dir="./hf_cache"):
        print(f"[INFO] Dang nap mo hinh: {model_name} (LoRA={use_lora})")

        # 1. Tokenizer: dùng AutoTokenizer cho cả ViT5 và BARTpho
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            use_fast=False,
            trust_remote_code=True,
        )

        # 2. Model
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            attn_implementation="eager",
        )

        # 3. Generation Config
        try:
            gen_config = GenerationConfig.from_pretrained(
                model_name,
                cache_dir=cache_dir,
            )
        except Exception:
            gen_config = GenerationConfig()

        # Default summarization config
        gen_config.max_length = 256
        gen_config.min_length = 30
        gen_config.num_beams = 4
        gen_config.pad_token_id = tokenizer.pad_token_id
        gen_config.eos_token_id = tokenizer.eos_token_id

        # decoder_start_token_id
        if "vit5" in model_name.lower():
            gen_config.decoder_start_token_id = tokenizer.pad_token_id
        else:
            gen_config.decoder_start_token_id = (
                tokenizer.bos_token_id
                if tokenizer.bos_token_id is not None
                else tokenizer.pad_token_id
            )

        model.generation_config = gen_config

        # 4. LoRA
        if use_lora:
            # In ra để xác nhận tên attention modules
            attn_modules = [
                name
                for name, _ in model.named_modules()
                if any(
                    k in name
                    for k in [
                        "q_proj",
                        "v_proj",
                        "k_proj",
                        "out_proj",
                        "fc1",
                        "fc2",
                        "q",
                        "v",
                        "query",
                        "value",
                    ]
                )
            ]
            print(
                f"[DEBUG] Attention modules found: {attn_modules[:10]} ... "
                f"(total: {len(attn_modules)})"
            )

            if "vit5" in model_name.lower():
                target_modules = ["q", "v"]
            else:
                target_modules = ["q_proj", "v_proj"]

            lora_config = LoraConfig(
                r=16,
                lora_alpha=32,
                target_modules=target_modules,
                lora_dropout=0.05,
                bias="none",
                task_type="SEQ_2_SEQ_LM",
            )

            model = get_peft_model(model, lora_config)
            model.print_trainable_parameters()

        return model, tokenizer