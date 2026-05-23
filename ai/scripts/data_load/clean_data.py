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

   

if __name__ == "__main__":
    process_cleaning()