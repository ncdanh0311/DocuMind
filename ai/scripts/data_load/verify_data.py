import os
from datasets import load_from_disk

def verify():
    paths = {
        "Summarization (Vietnews)": "datasets/processed/vietnews",
        "QA (ViQuAD)": "datasets/processed/viquad"
    }

    print("-" * 50)
    for task, path in paths.items():
        if os.path.exists(path):
            dataset = load_from_disk(path)
            print(f"Task: {task}")
            # In ra ten cac cot de kiem tra
            cols = dataset['train'].column_names
            print(f"  Columns: {cols}")
            
            for split in dataset.keys():
                print(f"  {split}: {len(dataset[split])} rows")
            
            print("\n  Sample data:")
            sample = dataset['train'][0]
            if "vietnews" in path:
                # Tu dong lay cot text va cot tom tat (du doan ten)
                article_col = 'article' if 'article' in cols else cols[0]
                # Kiem tra xem cot tom tat ten la 'abstract' hay 'summary'
                summary_col = 'abstract' if 'abstract' in cols else ('summary' if 'summary' in cols else cols[1])
                
                print(f"  Article: {sample[article_col][:150]}...")
                print(f"  Summary/Abstract: {sample[summary_col]}")
            else:
                print(f"  Context: {sample['context'][:150]}...")
                print(f"  Question: {sample['question']}")
                print(f"  Answer: {sample['answers']['text']}")
            print("-" * 50)
        else:
            print(f"Path not found: {path}")

def check_tokenizers():
    print("Checking Tokenizers:")
    base_path = "checkpoints"
    models = ["vit5_summarization", "phobert_qa"]
    for model in models:
        tok_path = os.path.join(base_path, model, "tokenizer")
        if os.path.exists(tok_path):
            files = os.listdir(tok_path)
            print(f"  {model}: OK ({len(files)} files)")
        else:
            print(f"  {model}: Missing")
    print("-" * 50)

if __name__ == "__main__":
    verify()
    check_tokenizers()