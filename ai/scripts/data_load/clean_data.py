import os
import re
from datasets import load_from_disk
from pyvi import ViTokenizer

def clean_common_noise(text):
    if not text: return ""
    # 1. Chuan hoa khoang trang
    text = re.sub(r'\s+', ' ', text).strip()
    # 2. Xoa cac ky tu la, chi giu lai chu, so va dau cau co ban
    text = re.sub(r'[^\w\s\d.,!?\-:;()_]', '', text)
    return text

def clean_vietnews(text):
    # Xoa cum tu ngay thang dau bai bao (Vi du: "Ngay 27/3 ,", "TP.HCM (TTO) -")
    text = re.sub(r'^(.*?)\s?-\s?', '', text) # Xoa phan dau den dau gach ngang
    text = re.sub(r'^Ngày \d+/\d+ , ', '', text) # Xoa "Ngay 27/3 ,"
    # Xoa ten phong vien/nguon tin o cuoi bai (thuong nam trong ngoac)
    text = re.sub(r'\(.*?\)$', '', text)
    return clean_common_noise(text)

def process_cleaning():
    print("Bat dau qua trinh lam sach du lieu...")
    
    # 1. Lam sach VIETNEWS
    sum_path = "datasets/processed/vietnews"
    if os.path.exists(sum_path):
        print("Dang xu ly Vietnews (co the mat vai phut)...")
        ds = load_from_disk(sum_path)
        
        def clean_sum_row(item):
            # Luu y: dung ten cot 'article' va 'abstract' ban da kiem tra
            item['article'] = clean_vietnews(item['article'])
            item['abstract'] = clean_vietnews(item['abstract'])
            return item
        
        ds_cleaned = ds.map(clean_sum_row, num_proc=4)
        # Loc bo cac bai qua ngan sau khi clean (duoi 20 tu)
        ds_cleaned = ds_cleaned.filter(lambda x: len(x['article'].split()) > 20)
        
        ds_cleaned.save_to_disk("datasets/cleaned/vietnews")
        print("Luu Vietnews sach tai: datasets/cleaned/vietnews")

    # 2. Lam sach VIQUAD
    qa_path = "datasets/processed/viquad"
    if os.path.exists(qa_path):
        print("Dang xu ly ViQuAD...")
        ds = load_from_disk(qa_path)
        
        def clean_qa_row(item):
            item['context'] = clean_common_noise(item['context'])
            item['question'] = clean_common_noise(item['question'])
            # Tach tu cho PhoBERT (Bat buoc phai co gach noi nhu Ha_Noi)
            item['context'] = ViTokenizer.tokenize(item['context'])
            item['question'] = ViTokenizer.tokenize(item['question'])
            # Luu y: Khong tach tu cho Answers vi se lam sai lech vi tri character start
            return item
        
        ds_cleaned = ds.map(clean_qa_row, num_proc=4)
        ds_cleaned.save_to_disk("datasets/cleaned/viquad")
        print("Luu ViQuAD sach tai: datasets/cleaned/viquad")

if __name__ == "__main__":
    process_cleaning()