import sys, os
sys.path.append('.')
import argparse
from src.models.build_qa import QAModelBuilder
import torch

def predict(model, tokenizer, question, context, max_length=384, doc_stride=96):
    inputs = tokenizer(
        question,
        context,
        max_length=max_length,
        truncation="only_second",
        stride=doc_stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
        return_tensors="pt",
    )

    offset_mapping   = inputs.pop("offset_mapping")
    sample_mapping   = inputs.pop("overflow_to_sample_mapping")
    sequence_ids_all = [inputs.sequence_ids(i) for i in range(len(inputs["input_ids"]))]

    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    best_score  = float("-inf")
    best_answer = ""

    for i in range(len(outputs.start_logits)):
        start_logits = outputs.start_logits[i]
        end_logits   = outputs.end_logits[i]
        offsets      = offset_mapping[i]
        seq_ids      = sequence_ids_all[i]

        # Chỉ xét token thuộc context (seq_id == 1)
        for start_idx in range(len(start_logits)):
            if seq_ids[start_idx] != 1:
                continue
            for end_idx in range(start_idx, min(start_idx + 30, len(end_logits))):
                if seq_ids[end_idx] != 1:
                    continue
                score = start_logits[start_idx] + end_logits[end_idx]
                if score > best_score:
                    best_score  = score
                    char_start  = offsets[start_idx][0].item()
                    char_end    = offsets[end_idx][1].item()
                    best_answer = context[char_start:char_end]

    return best_answer, best_score.item()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to best_model")
    parser.add_argument("--max_length", type=int, default=384)
    parser.add_argument("--doc_stride", type=int, default=96)
    args = parser.parse_args()

    model, tokenizer = QAModelBuilder.build(args.model)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    print(f"[INFO] Model loaded, device: {device}")
    print("=" * 60)

    while True:
        print("\nNhap context (Enter 2 lan de ket thuc):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        context = " ".join(lines).strip()
        if not context:
            print("Thoat.")
            break

        while True:
            question = input("\nCau hoi (Enter de doi context): ").strip()
            if not question:
                break
            answer, score = predict(
                model, tokenizer, question, context,
                args.max_length, args.doc_stride
            )
            print(f"Tra loi: {answer}")
            print(f"Score:   {score:.4f}")

if __name__ == "__main__":
    main()
