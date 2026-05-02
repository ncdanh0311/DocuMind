import os
from huggingface_hub import snapshot_download

# Ép lưu vào thư mục cache của dự án
CACHE_DIR = os.path.abspath("./hf_cache")

def download_vit5_only():
    print("--- Đang tải riêng ViT5 bằng snapshot (Bỏ qua lỗi khởi tạo) ---")
    try:
        snapshot_download(
            repo_id="VietAI/vit5-base",
            local_files_only=False,
            cache_dir=CACHE_DIR,
            # Chỉ tải các file cần thiết
            allow_patterns=["*.json", "*.bin", "*.model", "*.safetensors"]
        )
        print("\n✓ THÀNH CÔNG: Đã tải xong ViT5 về hf_cache.")
        print("Lỗi 'vocab' sẽ không còn quan trọng vì file đã nằm trên ổ cứng của bạn.")
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    download_vit5_only()