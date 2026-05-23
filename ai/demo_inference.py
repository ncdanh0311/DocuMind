import os
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForQuestionAnswering,
    GenerationConfig,
    T5Tokenizer,
)

from peft import PeftModel

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
HF_CACHE = os.path.join(ROOT_DIR, "hf_cache")


# =========================================================
# MODEL CONFIG
# =========================================================

MODELS = {
    "1": {
        "name": "BARTpho - Tóm tắt",
        "type": "summarization",
        "best_model": "results/models/bartpho_summarization/best_model",
        "base": "vinai/bartpho-word-base",
        "is_vit5": False,
    },
    "2": {
        "name": "ViT5 - Tóm tắt",
        "type": "summarization",
        "best_model": "results/models/vit5_summarization/best_model",
        "base": "VietAI/vit5-base",
        "is_vit5": True,
    },
    "3": {
        "name": "PhoBERT - QA",
        "type": "qa",
        "best_model": "results/models/phobert_qa/best_model",
        "base": "vinai/phobert-base",
        "max_length": 256,
    },
    "4": {
        "name": "XLM-RoBERTa - QA",
        "type": "qa",
        "best_model": "results/models/xlmroberta_qa/best_model",
        "base": "xlm-roberta-base",
        "max_length": 512,
    },
}


# =========================================================
# TOKENIZER
# =========================================================

def load_tokenizer(base_model_name, is_vit5=False):

    print(f"→ Load tokenizer: {base_model_name}")

    if is_vit5:
        return T5Tokenizer.from_pretrained(
            base_model_name,
            cache_dir=HF_CACHE,
            use_fast=False,
            legacy=True
        )

    return AutoTokenizer.from_pretrained(
        base_model_name,
        cache_dir=HF_CACHE,
        use_fast=False
    )


# =========================================================
# SUMMARIZATION MODEL
# =========================================================

def load_sum_model(model_info):

    base = model_info["base"]
    path = model_info["best_model"]
    is_vit5 = model_info["is_vit5"]

    tokenizer = load_tokenizer(base, is_vit5)

    # ===================== FIX TOKEN =====================
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("→ Load summarization model")

    base_model = AutoModelForSeq2SeqLM.from_pretrained(
        base,
        cache_dir=HF_CACHE,
        torch_dtype=torch.float32,
        attn_implementation="eager",
    )

    model = PeftModel.from_pretrained(base_model, path)
    model = model.merge_and_unload()
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    # ===================== GENERATION FIX =====================
    gen_config = GenerationConfig()

    gen_config.max_new_tokens = 128
    gen_config.min_length = 20
    gen_config.num_beams = 5
    gen_config.do_sample = False
    gen_config.early_stopping = True
    gen_config.repetition_penalty = 1.3
    gen_config.no_repeat_ngram_size = 3

    gen_config.pad_token_id = tokenizer.pad_token_id
    gen_config.eos_token_id = tokenizer.eos_token_id

    # 🔥 FIX QUAN TRỌNG CHO ViT5
    gen_config.decoder_start_token_id = tokenizer.eos_token_id

    model.generation_config = gen_config

    print(f"→ Model ready on {device}")

    return model, tokenizer, device


# =========================================================
# QA MODEL
# =========================================================

def load_qa_model(model_info):

    base = model_info["base"]
    path = model_info["best_model"]

    tokenizer = load_tokenizer(base)

    print("→ Load QA model")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    adapter_config = os.path.join(path, "adapter_config.json")

    if os.path.exists(adapter_config):

        base_model = AutoModelForQuestionAnswering.from_pretrained(
            base,
            cache_dir=HF_CACHE,
            torch_dtype=torch.float32,
        )

        model = PeftModel.from_pretrained(base_model, path)
        model = model.merge_and_unload()

    else:
        model = AutoModelForQuestionAnswering.from_pretrained(
            path,
            cache_dir=HF_CACHE,
            torch_dtype=torch.float32,
        )

    model.eval()
    model = model.to(device)

    print(f"→ QA ready on {device}")

    return model, tokenizer, device


# =========================================================
# SUMMARIZATION RUN
# =========================================================

def run_summarization(model, tokenizer, device):

    print("\n📄 INPUT TEXT:")

    lines = []
    while True:
        x = input()
        if x == "":
            break
        lines.append(x)

    text = " ".join(lines).strip()

    if not text:
        print("Empty input")
        return

    # 🔥 CLEAN TEXT
    text = " ".join(text.split())

    input_text = "summarize: " + text

    inputs = tokenizer(
        input_text,
        max_length=768,
        truncation=True,
        return_tensors="pt",
    ).to(device)

    inputs.pop("token_type_ids", None)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=128,
            num_beams=5,
            do_sample=False,
            repetition_penalty=1.3,
            no_repeat_ngram_size=3,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    result = tokenizer.decode(output[0], skip_special_tokens=True)
    result = result.replace("_", " ").strip()

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("=" * 50)
    print(result)
    print("=" * 50)


# =========================================================
# QA RUN
# =========================================================

def run_qa(model, tokenizer, device, max_length):

    print("\nCONTEXT:")

    lines = []
    while True:
        x = input()
        if x == "":
            break
        lines.append(x)

    context = " ".join(lines)
    context = " ".join(context.split())

    print("\nQUESTION:")
    question = input().strip()

    inputs = tokenizer(
        question,
        context,
        max_length=max_length,
        truncation=True,
        return_tensors="pt"
    ).to(device)

    inputs.pop("token_type_ids", None)

    with torch.no_grad():
        outputs = model(**inputs)

    start = torch.argmax(outputs.start_logits)
    end = torch.argmax(outputs.end_logits) + 1

    answer = tokenizer.decode(
        inputs["input_ids"][0][start:end],
        skip_special_tokens=True
    )

    print("\nANSWER:")
    print(answer.strip() if answer else "(no answer)")


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n=== MODELS ===")
    for k, v in MODELS.items():
        print(k, v["name"])
    print("0 exit")

    loaded = {}

    while True:

        choice = input("choice: ").strip()

        if choice == "0":
            break

        if choice not in MODELS:
            continue

        cfg = MODELS[choice]

        if choice not in loaded:

            if cfg["type"] == "summarization":
                model, tok, dev = load_sum_model(cfg)
                loaded[choice] = (model, tok, dev)

            else:
                model, tok, dev = load_qa_model(cfg)
                loaded[choice] = (model, tok, dev, cfg["max_length"])

        print("\n📄 INPUT TEXT:")

        if cfg["type"] == "summarization":
            model, tok, dev = loaded[choice]
            run_summarization(model, tok, dev)

        else:
            model, tok, dev, ml = loaded[choice]
            run_qa(model, tok, dev, ml)


if __name__ == "__main__":
    main()