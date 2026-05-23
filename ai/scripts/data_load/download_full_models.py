import os
import sys
from pathlib import Path

# --- CẤU HÌNH ĐƯỜNG DẪN CACHE ---
# Ép dùng thư mục hf_cache ngay trong dự án để tránh lỗi quyền ghi ở ổ D:\ gốc
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "hf_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Thiết lập biến môi trường cho cả hệ thống và thư viện
os.environ["HF_HOME"] = str(CACHE_DIR)

try:
    import torch
    from transformers import (
        AutoModelForSeq2SeqLM, 
        AutoModelForQuestionAnswering, 
        AutoTokenizer,
        T5Tokenizer
    )
except ImportError:
    print("Lỗi: Thiếu thư viện. Hãy chạy: pip install transformers torch")
    sys.exit(1)

def download_single_model(label, model_id, model_class):
    print(f"\n[+] Đang tải {label}: {model_id}...")
    try:
        # 1. Xử lý Tokenizer (Dùng use_fast=False để sửa lỗi Vocab dict trên Windows)
        print(f"    - Đang tải Tokenizer...")
        if "vit5" in model_id.lower():
            tokenizer = T5Tokenizer.from_pretrained(
                model_id, 
                cache_dir=str(CACHE_DIR),
                use_fast=False,
                trust_remote_code=True
            )
        else:
            tokenizer = AutoTokenizer.from_pretrained(
                model_id, 
                cache_dir=str(CACHE_DIR),
                use_fast=False,
                trust_remote_code=True
            )
        
        # 2. Xử lý Model (Dùng use_safetensors=True để sửa lỗi bảo mật CVE-2025)
        print(f"    - Đang tải Trọng số (Weights)...")
        model = model_class.from_pretrained(
            model_id,
            cache_dir=str(CACHE_DIR),
            trust_remote_code=True,
            use_safetensors=True # Ép dùng định dạng an toàn
        )
        print(f"    => THÀNH CÔNG: {model_id}")
        return True
    except Exception as e:
        print(f"    => LỖI tại {model_id}: {str(e)}")
        return False

def main():
    print("="*60)
    print("VIETSUMBOT - DOWNLOAD FULL MODELS (MAIN + BASELINES)")
    print(f"Lưu tại: {CACHE_DIR}")
    print("="*60)

    # Danh sách 4 model: 2 chính, 2 đối thủ
    models = [
        ("Summarization (CHÍNH)", "VietAI/vit5-base", AutoModelForSeq2SeqLM),
        ("QA/NER (CHÍNH)", "vinai/phobert-base", AutoModelForQuestionAnswering),
        ("Summarization (ĐỐI THỦ)", "vinai/bartpho-word-base", AutoModelForSeq2SeqLM),
        ("QA/NER (ĐỐI THỦ)", "xlm-roberta-base", AutoModelForQuestionAnswering)
    ]

    success_count = 0
    for label, m_id, m_class in models:
        if download_single_model(label, m_id, m_class):
            success_count += 1

    print("\n" + "="*60)
    print(f"HOÀN TẤT: Đã tải thành công {success_count}/{len(models)} models.")
    print(f"Bây giờ bạn có thể copy toàn bộ thư mục '{BASE_DIR.name}' lên Server GPU.")
    print("="*60)

if __name__ == "__main__":
    main()