import os
import sys
import shutil
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datasets import load_from_disk
import pandas as pd

# Cau hinh matplotlib
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.style.use('ggplot')

def clear_old_results(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    print(f"Da xoa va lam moi thu muc: {path}")

def visualize_summarization():
    print("--- Dang phan tich du lieu tom tat (Vietnews) ---")
    path = "datasets/processed/vietnews"
    if not os.path.exists(path):
        print("Bo qua: Khong tim thay vietnews")
        return

    try:
        dataset = load_from_disk(path)
        lengths = []
        for split in dataset.keys():
            subset_size = min(1000, len(dataset[split]))
            subset = dataset[split].select(range(subset_size))
            for item in subset:
                # Kiem tra cac truong du lieu co ton tai khong
                if item.get('article') and item.get('abstract'):
                    article_len = len(item['article'].split())
                    summary_len = len(item['abstract'].split())
                    lengths.append({
                        'split': split,
                        'article_words': article_len,
                        'summary_words': summary_len
                    })

        df = pd.DataFrame(lengths)
        if not df.empty:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            sns.histplot(data=df, x='article_words', hue='split', ax=axes[0], kde=True)
            axes[0].set_title('Do dai bai viet (so tu)')
            sns.histplot(data=df, x='summary_words', hue='split', ax=axes[1], kde=True)
            axes[1].set_title('Do dai tom tat (so tu)')
            plt.tight_layout()
            plt.savefig('results/images/summarization_stats.png')
            print("Luu thanh cong: summarization_stats.png")
    except Exception as e:
        print(f"Loi Vietnews: {e}")

def visualize_qa():
    print("--- Dang phan tich du lieu hoi dap (ViQuAD) ---")
    path = "datasets/processed/viquad"
    if not os.path.exists(path):
        print("Bo qua: Khong tim thay viquad")
        return

    try:
        dataset = load_from_disk(path)
        lengths = []
        for split in dataset.keys():
            subset_size = min(1000, len(dataset[split]))
            subset = dataset[split].select(range(subset_size))
            
            for item in subset:
                # KIEM TRA CHAT CHE: answers phai ton tai va la dictionary
                context_len = len(item['context'].split()) if item.get('context') else 0
                question_len = len(item['question'].split()) if item.get('question') else 0
                
                answer_len = 0
                # Sua loi 'NoneType' object is not subscriptable tai day
                if item.get('answers') is not None and isinstance(item['answers'], dict):
                    ans_text = item['answers'].get('text', [])
                    if ans_text and len(ans_text) > 0:
                        answer_len = len(str(ans_text[0]).split())
                
                lengths.append({
                    'split': split,
                    'context_words': context_len,
                    'question_words': question_len,
                    'answer_words': answer_len
                })

        df = pd.DataFrame(lengths)
        if not df.empty:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            sns.histplot(data=df, x='context_words', hue='split', ax=axes[0], kde=True)
            axes[0].set_title('Do dai ngu canh (so tu)')
            sns.histplot(data=df, x='question_words', hue='split', ax=axes[1], kde=True)
            axes[1].set_title('Do dai cau hoi (so tu)')
            plt.tight_layout()
            plt.savefig('results/images/qa_stats.png')
            print("Luu thanh cong: qa_stats.png")
    except Exception as e:
        print(f"Loi ViQuAD: {e}")

def main():
    img_path = 'results/images'
    clear_old_results(img_path)
    visualize_summarization()
    visualize_qa()
    print("Hoan thanh! Ket qua tai results/images/")

if __name__ == "__main__":
    main()