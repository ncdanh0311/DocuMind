from transformers import AutoTokenizer, AutoModelForQuestionAnswering

class QAModelBuilder:
    @staticmethod
    def build(model_name, cache_dir="./hf_cache"):
        print(f"[INFO] Dang nap mo hinh QA: {model_name}")
        # Su dung use_fast=True de ho tro offset_mapping
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            cache_dir=cache_dir, 
            use_fast=True 
        )
        model = AutoModelForQuestionAnswering.from_pretrained(model_name, cache_dir=cache_dir)
        return model, tokenizer