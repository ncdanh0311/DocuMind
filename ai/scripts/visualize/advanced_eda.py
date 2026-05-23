import os
from datasets import load_from_disk
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd
import seaborn as sns
from pyvi import ViTokenizer
import re

# Tu dien tu dung (Stop words) co ban de loc bo cac tu vo nghia
STOP_WORDS = set([
    "và", "là", "của", "để", "trong", "các", "đã", "được", "cho", "tại", "có", 
    "đến", "với", "theo", "những", "này", "về", "như", "nhiều", "nhưng", "khi",
    "một", "hai", "ba", "vừa", "qua", "sau", "trên", "dưới", "nói", "cho_biết",
    "đang", "còn", "ra", "đến", "lại", "nữa", "phải", "đến", "bị", "con", "cái"
])

def clean_and_tokenize(text):
    # Lam sach nhe
    text = re.sub(r'[^\w\s]', '', str(text).lower())
    # Tach tu: "Hà Nội" -> "Hà_Nội"
    tokens = ViTokenizer.tokenize(text).split()
    # Loc stop words va tu qua ngan
    return [t for t in tokens if t not in STOP_WORDS and "_" in t or len(t) > 2]

def get_ngrams(tokens, n=2):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def process_eda():
    output_dir = 'results/images/eda'
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. PHAN TICH VIETNEWS (TOM TAT)
    print("Dang phan tich noi dung Vietnews...")
    ds_sum = load_from_disk("datasets/processed/vietnews")
    # Lay mau 2000 dong de phan tich cho nhanh
    sample_sum = ds_sum['train'].select(range(min(2000, len(ds_sum['train']))))
    
    all_words = []
    all_bigrams = []
    
    for item in sample_sum:
        tokens = clean_and_tokenize(item['article'])
        all_words.extend(tokens)
        all_bigrams.extend(get_ngrams(tokens, 2))

    # Ve Word Cloud cho Vietnews
    wordcloud = WordCloud(width=800, height=400, background_color='white', 
                          max_words=100, colormap='viridis').generate(" ".join(all_words))
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud - Noi dung Vietnews')
    plt.savefig(f'{output_dir}/vietnews_wordcloud.png')
    plt.close()

    # Ve Top 20 Bigrams cho Vietnews
    bigram_counts = Counter(all_bigrams).most_common(20)
    df_bigrams = pd.DataFrame(bigram_counts, columns=['Phrase', 'Count'])
    plt.figure(figsize=(10, 8))
    sns.barplot(data=df_bigrams, x='Count', y='Phrase', palette='magma')
    plt.title('Top 20 Cum tu (Bigrams) pho bien nhat trong Vietnews')
    plt.savefig(f'{output_dir}/vietnews_bigrams.png')
    plt.close()

    # 2. PHAN TICH VIQUAD (HOI DAP)
    print("Dang phan tich noi dung ViQuAD...")
    ds_qa = load_from_disk("datasets/processed/viquad")
    sample_qa = ds_qa['train'].select(range(min(2000, len(ds_qa['train']))))
    
    qa_words = []
    for item in sample_qa:
        qa_words.extend(clean_and_tokenize(item['question']))

    # Ve Word Cloud cho cau hoi trong ViQuAD
    wordcloud_qa = WordCloud(width=800, height=400, background_color='black', 
                             max_words=50, colormap='spring').generate(" ".join(qa_words))
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud_qa, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud - Cac tu hay gap trong Cau hoi ViQuAD')
    plt.savefig(f'{output_dir}/viquad_question_cloud.png')
    plt.close()

    print(f"Hoan thanh! Anh duoc luu tai: {output_dir}")

if __name__ == "__main__":
    process_eda()