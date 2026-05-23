#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import argparse
import logging
from huggingface_hub import login, hf_hub_download

# --- CẤU HÌNH HỆ THỐNG ---
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["HF_HOME"] = str(BASE_DIR / "hf_cache")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from datasets import load_dataset
from transformers import T5Tokenizer, AutoTokenizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_auth():
    """Tự động đăng nhập bằng Token trong .env"""
    try:
        with open(".env", "r") as f:
            for line in f:
                if "HF_TOKEN" in line:
                    token = line.split("=")[1].strip()
                    login(token=token)
                    return True
    except:
        logger.error("❌ Không tìm thấy HF_TOKEN trong file .env")
    return False

def download_vietnews(output_dir):
    """Tải Vietnews từ nguồn nam194 (Dạng Parquet - Rất ổn định)"""
    path = Path(output_dir) / "vietnews"
    if path.exists():
        logger.info("✓ Dữ liệu Vietnews đã có sẵn.")
        return True

    logger.info("--- Đang tải Vietnews (Tóm tắt - Nguồn nam194) ---")
    try:
        # Tải bản nam194/vietnews (Không cần trust_remote_code)
        dataset = load_dataset("nam194/vietnews")
        dataset.save_to_disk(str(path))
        logger.info(f"✓ Đã lưu Vietnews tại: {path}")
        return True
    except Exception as e:
        logger.error(f"Lỗi tải Vietnews: {e}")
        return False

def download_tokenizers(output_dir):
    """Tải Tokenizers và sửa lỗi 'vocab dict' trên Windows"""
    logger.info("--- Đang tải Tokenizers ---")
    
    # 1. ViT5 Tokenizer (Tải thủ công file spiece.model để tránh lỗi)
    try:
        vit5_path = Path(output_dir) / "vit5_summarization" / "tokenizer"
        if not vit5_path.exists():
            logger.info("Đang tải ViT5 Tokenizer...")
            vit5_path.mkdir(parents=True, exist_ok=True)
            hf_hub_download(repo_id="VietAI/vit5-base", filename="spiece.model", local_dir=str(vit5_path))
            hf_hub_download(repo_id="VietAI/vit5-base", filename="tokenizer_config.json", local_dir=str(vit5_path))
            hf_hub_download(repo_id="VietAI/vit5-base", filename="config.json", local_dir=str(vit5_path))
            
            tokenizer = T5Tokenizer.from_pretrained(str(vit5_path), use_fast=False)
            tokenizer.save_pretrained(str(vit5_path))
            logger.info("✓ Đã lưu ViT5 Tokenizer thành công.")
        else:
            logger.info("✓ ViT5 Tokenizer đã có sẵn.")
    except Exception as e:
        logger.error(f"Lỗi tải ViT5 Tokenizer: {e}")

    # 2. PhoBERT Tokenizer (Bạn đã tải được rồi, bước này kiểm tra lại)
    try:
        pb_path = Path(output_dir) / "phobert_qa" / "tokenizer"
        if not pb_path.exists():
            logger.info("Đang tải PhoBERT Tokenizer...")
            tokenizer_pb = AutoTokenizer.from_pretrained("vinai/phobert-base", use_fast=False)
            tokenizer_pb.save_pretrained(str(pb_path))
            logger.info("✓ Đã lưu PhoBERT Tokenizer.")
        else:
            logger.info("✓ PhoBERT Tokenizer đã có sẵn.")
    except Exception as e:
        logger.error(f"Lỗi tải PhoBERT Tokenizer: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if not setup_auth(): return

    data_dir = "datasets/processed"
    ckp_dir = "checkpoints"
    
    if args.all:
        download_vietnews(data_dir)
        download_tokenizers(ckp_dir)
        logger.info("--- HOÀN TẤT TẤT CẢ QUÁ TRÌNH TẢI ---")

if __name__ == "__main__":
    main()