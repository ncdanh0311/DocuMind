import torch
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, T5Tokenizer
from peft import PeftModel

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def chat_interface():
    print("="*50)
    print(" CHỌN MÔ HÌNH ĐỂ TEST TÓM TẮT ")
    print(" 1. BARTpho")
    print(" 2. ViT5")
    print("="*50)
    choice = input("Nhập số 1 hoặc 2: ").strip()

    # THIẾT LẬP ĐƯỜNG DẪN TƯƠNG ỨNG
    if choice == "1":
        base_name = "vinai/bartpho-word-base"
        # Sửa chữ 'best' thành folder chứa model của bạn nếu cần (vd: best_model, checkpoint-xxxx)
        model_path = "results/models/bartpho_summarization/best" 
        is_vit5 = False
    elif choice == "2":
        base_name = "VietAI/vit5-base"
        model_path = "results/models/vit5_summarization/best"
        is_vit5 = True
    else:
        print("Lựa chọn không hợp lệ!")
        return

    if not os.path.exists(model_path):
        print(f"\n[LỖI] Không tìm thấy thư mục: {model_path}")
        print("Hãy kiểm tra lại xem model của bạn đang lưu ở 'best' hay 'best_model' hay 'checkpoint-xxxx'")
        return

    print(f"\n[INFO] Đang nạp não gốc từ {base_name}...")
    
    # 1. LOAD TOKENIZER (Dùng cấu hình an toàn nhất bạn đã test thành công)
    if is_vit5:
        tokenizer = T5Tokenizer.from_pretrained(base_name, cache_dir="./hf_cache", use_fast=False, legacy=True)
    else:
        tokenizer = AutoTokenizer.from_pretrained(base_name, cache_dir="./hf_cache", use_fast=False)

    # 2. LOAD BASE MODEL
    base_model = AutoModelForSeq2SeqLM.from_pretrained(
        base_name, 
        cache_dir="./hf_cache",
        torch_dtype=torch.float32, # Dùng float32 cho an toàn tuyệt đối khi inference
        trust_remote_code=True
    )

    # 3. NẠP LORA
    print(f"[INFO] Đang nạp phần chất xám LoRA từ {model_path}...")
    model = PeftModel.from_pretrained(base_model, model_path).to(DEVICE)
    model = model.merge_and_unload()
    model.eval()
    
    print("\n" + "="*50)
    print("✅ MÔ HÌNH ĐÃ SẴN SÀNG!")
    print("Hãy Copy bài báo và Dán (Paste) vào đây.")
    print("Lưu ý: Dán xong, hãy nhấn phím ENTER 2 LẦN để máy bắt đầu chạy. Gõ 'q' để thoát.")
    print("="*50)

    while True:
        print("\n📄 NHẬP BÀI BÁO:")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        text = " ".join(lines).strip()
        
        if text.lower() == 'q':
            break
        if not text:
            continue

        # Thêm prefix cho ViT5
        input_text = "summarize: " + text if is_vit5 else text

        inputs = tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True).to(DEVICE)
        
        # Xóa token_type_ids để chống sập CUDA
        if "token_type_ids" in inputs:
            inputs.pop("token_type_ids")

        print("\n⏳ AI ĐANG TÓM TẮT...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,        # Đảm bảo độ dài tóm tắt đủ dài (không bị 21 từ nữa)
                min_length=30,
                num_beams=5,
                repetition_penalty=1.5,
                no_repeat_ngram_size=3,
                early_stopping=True,
                decoder_start_token_id=tokenizer.pad_token_id if is_vit5 else tokenizer.bos_token_id
            )

        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Xóa dấu gạch dưới của BARTpho
        summary = summary.replace("_", " ")

        print("\n" + "="*50)
        print("📝 KẾT QUẢ TÓM TẮT:")
        print(summary)
        print("="*50)

if __name__ == "__main__":
    chat_interface()