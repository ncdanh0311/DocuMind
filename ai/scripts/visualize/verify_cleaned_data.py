import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datasets import load_from_disk

# Cau hinh hien thi bieu do
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.style.use('ggplot')

def check_segmentation(text):
    """Kiem tra xem van ban da co dau gach duoi (_) cua segmentation chua"""
    if not text: return False
    return "_" in str(text)

def verify_cleaned_summarization():
    print("--- Kiem tra du lieu Tom tat (Cleaned) ---")
    path = "datasets/cleaned/vietnews"
    if not os.path.exists(path):
        print("Loi: Khong tim thay thu muc vietnews da lam sach")
        return None

    ds = load_from_disk(path)
    stats = []
    
    for split in ds.keys():
        print(f"Split {split}: {len(ds[split])} rows")
        # Lay mau 1000 dong de thong ke
        sample_size = min(1000, len(ds[split]))
        df_sample = pd.DataFrame(ds[split].select(range(sample_size)))
        
        for _, row in df_sample.iterrows():
            stats.append({
                'split': split,
                'task': 'Summarization',
                'article_len': len(str(row['article']).split()),
                'abstract_len': len(str(row['abstract']).split())
            })
            
    # Hien thi 2 dong dau de xem noi dung chu viet
    print("Noi dung mau (da lam sach):")
    sample_row = ds['train'][0]
    print(f"Article (100 ky tu): {sample_row['article'][:100]}...")
    print(f"Abstract: {sample_row['abstract'][:100]}...")
    
    return pd.DataFrame(stats)

def verify_cleaned_qa():
    print("\n--- Kiem tra du lieu Hoi dap (Cleaned) ---")
    path = "datasets/cleaned/viquad"
    if not os.path.exists(path):
        print("Loi: Khong tim thay thu muc viquad da lam sach")
        return None

    ds = load_from_disk(path)
    stats = []
    
    # Lay 1 mau bat ky de kiem tra segmentation
    sample_item = ds['train'][0]
    is_segmented = check_segmentation(sample_item['context'])
    print(f"Trang thai tach tu (Segmentation): {'Thanh cong' if is_segmented else 'Chua thuc hien'}")

    for split in ds.keys():
        print(f"Split {split}: {len(ds[split])} rows")
        sample_size = min(1000, len(ds[split]))
        df_sample = pd.DataFrame(ds[split].select(range(sample_size)))
        
        for _, row in df_sample.iterrows():
            # SUA LOI TAI DAY: Kiem tra answers co bi None khong
            ans_len = 0
            if row['answers'] is not None and isinstance(row['answers'], dict):
                ans_text = row['answers'].get('text', [])
                if ans_text and len(ans_text) > 0:
                    ans_len = len(str(ans_text[0]).split())
            
            stats.append({
                'split': split,
                'task': 'QA',
                'context_len': len(str(row['context']).split()) if row['context'] else 0,
                'question_len': len(str(row['question']).split()) if row['question'] else 0,
                'answer_len': ans_len
            })

    return pd.DataFrame(stats)
    print("\n--- Kiem tra du lieu Hoi dap (Cleaned) ---")
    path = "datasets/cleaned/viquad"
    if not os.path.exists(path):
        print("Loi: Khong tim thay thu muc viquad da lam sach")
        return None

    ds = load_from_disk(path)
    stats = []
    
    # Kiem tra segmentation tren 1 dong mau
    sample_text = ds['train'][0]['context']
    is_segmented = check_segmentation(sample_text)
    print(f"Trang thai tach tu (Segmentation): {'Thanh cong' if is_segmented else 'Chua thuc hien'}")

    for split in ds.keys():
        print(f"Split {split}: {len(ds[split])} rows")
        sample_size = min(1000, len(ds[split]))
        df_sample = pd.DataFrame(ds[split].select(range(sample_size)))
        
        for _, row in df_sample.iterrows():
            ans_text = row['answers']['text']
            ans_len = len(str(ans_text[0]).split()) if (ans_text and len(ans_text) > 0) else 0
            stats.append({
                'split': split,
                'task': 'QA',
                'context_len': len(str(row['context']).split()),
                'question_len': len(str(row['question']).split()),
                'answer_len': ans_len
            })

    return pd.DataFrame(stats)

def plot_cleaned_stats(df_sum, df_qa):
    print("\n--- Dang ve bieu do thong ke moi ---")
    output_path = "results/images/cleaned_data_stats.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(15, 12))

    # 1. Do dai Vietnews Article
    if df_sum is not None:
        sns.histplot(data=df_sum, x='article_len', hue='split', ax=axes[0,0], kde=True)
        axes[0,0].set_title('Vietnews: Do dai Article (Cleaned)')

        # 2. Do dai Vietnews Abstract
        sns.histplot(data=df_sum, x='abstract_len', hue='split', ax=axes[0,1], kde=True)
        axes[0,1].set_title('Vietnews: Do dai Abstract (Cleaned)')

    # 3. Do dai ViQuAD Context
    if df_qa is not None:
        sns.histplot(data=df_qa, x='context_len', hue='split', ax=axes[1,0], kde=True)
        axes[1,0].set_title('ViQuAD: Do dai Context (Cleaned)')

        # 4. Do dai ViQuAD Question
        sns.histplot(data=df_qa, x='question_len', hue='split', ax=axes[1,1], kde=True)
        axes[1,1].set_title('ViQuAD: Do dai Question (Cleaned)')

    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Da luu bieu do tai: {output_path}")

def main():
    print("BAT DAU KIEM TRA DU LIEU SAU KHI LAM SACH")
    print("="*50)
    
    df_sum = verify_cleaned_summarization()
    df_qa = verify_cleaned_qa()
    
    plot_cleaned_stats(df_sum, df_qa)
    
    print("="*50)
    print("KET THUC KIEM TRA")

if __name__ == "__main__":
    main()