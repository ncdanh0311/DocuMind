import os
import pandas as pd
from datasets import load_from_disk

# Cau hinh de hien thi bang dep hon trong Terminal
pd.set_option('display.max_colwidth', 80)
pd.set_option('display.width', 1000)

def peek_summarization():
    path = "datasets/processed/vietnews"
    if not os.path.exists(path): return
    
    print("\n" + "="*40)
    print(" BANG DU LIEU TOM TAT (VIETNEWS) ")
    print("="*40)
    
    ds = load_from_disk(path)
    # Lay 3 dong dau tien
    df = pd.DataFrame(ds['train'].select(range(3)))
    
    # Chi lay cot Article va Abstract de hien thi
    df_show = df[['article', 'abstract']].copy()
    # Rut ngan bot chu de bang khoi bi vo
    df_show['article'] = df_show['article'].str.slice(0, 150) + "..."
    df_show['abstract'] = df_show['abstract'].str.slice(0, 100) + "..."
    
    print(df_show.to_string(index=False))

def peek_qa():
    path = "datasets/processed/viquad"
    if not os.path.exists(path): return
    
    print("\n" + "="*40)
    print(" BANG DU LIEU HOI DAP (VIQUAD) ")
    print("="*40)
    
    ds = load_from_disk(path)
    samples = ds['train'].select(range(3))
    
    data = []
    for item in samples:
        ans = item['answers']['text'][0] if item['answers']['text'] else "No Answer"
        data.append({
            "Context (Ngu canh)": item['context'][:150] + "...",
            "Question (Cau hoi)": item['question'],
            "Answer (Dap an)": ans
        })
    
    df = pd.DataFrame(data)
    print(df.to_string(index=False))

if __name__ == "__main__":
    peek_summarization()
    peek_qa()