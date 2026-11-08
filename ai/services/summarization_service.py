from ai.runtime.models import runtime

class SummarizationService:
    def summarize(self, text, model_type="vit5", expected_version=None, max_output_tokens=128):
        import torch
        with runtime.lock:
            manifest, tokenizer, model, device = runtime.load(model_type)
            if expected_version and expected_version != manifest.version: raise ValueError("ERR_MODEL_VERSION_CHANGED")
            prepared = runtime.preprocess(manifest, text)
            inputs = tokenizer(prepared, return_tensors="pt", truncation=False)
            if inputs.input_ids.shape[1] > manifest.max_input_tokens: raise ValueError("ERR_TOKEN_BUDGET")
            inputs.pop("token_type_ids", None)
            inputs = inputs.to(device)
            target = min(max_output_tokens, manifest.max_output_tokens)
            with torch.inference_mode():
                output = model.generate(**inputs, **manifest.generation, max_new_tokens=target, min_new_tokens=min(16, target // 2))
            result = tokenizer.decode(output[0], skip_special_tokens=True)
            if manifest.preprocessing == "bartpho": result = result.replace("_", " ")
            return {"summary": result.strip(), "model_version": manifest.version}

summarization_service = SummarizationService()
