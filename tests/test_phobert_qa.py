import sys
import os
import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering

# Đảm bảo import được pyvi
try:
    from pyvi import ViTokenizer
except ImportError:
    print("⚠️ Không tìm thấy thư viện 'pyvi'. Vui lòng cài đặt bằng cách chạy: pip install pyvi")
    sys.exit(1)

# Đường dẫn đến model PhoBERT QA đã finetune
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai/results/models/phobert_qa/best_model"))

def load_qa_model():
    print(f"📦 Đang tải mô hình PhoBERT QA từ: {MODEL_PATH}...")
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Lỗi: Thư mục mô hình không tồn tại tại {MODEL_PATH}")
        sys.exit(1)
        
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"💻 Sử dụng thiết bị: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForQuestionAnswering.from_pretrained(MODEL_PATH).to(device)
    return model, tokenizer, device

def answer_question(model, tokenizer, device, context: str, question: str) -> str:
    # 1. Tách từ (Word Segmentation) bằng ViTokenizer cho PhoBERT
    segmented_context = ViTokenizer.tokenize(context)
    segmented_question = ViTokenizer.tokenize(question)
    
    # 2. Tokenize dữ liệu đầu vào
    inputs = tokenizer(
        segmented_question, 
        segmented_context, 
        return_tensors="pt", 
        truncation=True, 
        max_length=258 # max_position_embeddings của PhoBERT QA này là 258
    ).to(device)
    
    # 3. Chạy model dự báo
    with torch.no_grad():
        outputs = model(**inputs)
        
    # 4. Xác định vị trí các token thuộc về context thủ công bằng cách tìm các token EOS (2)
    # Định dạng đầu vào của PhoBERT/RoBERTa khi nhập 2 chuỗi là: <s> question </s> </s> context </s>
    input_ids = inputs.input_ids[0].tolist()
    eos_token_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 2
    eos_indices = [i for i, token_id in enumerate(input_ids) if token_id == eos_token_id]
    
    if len(eos_indices) >= 2:
        # Context bắt đầu ngay sau dấu EOS thứ 2 và kết thúc trước dấu EOS cuối cùng
        context_start = eos_indices[1] + 1
        context_end = eos_indices[-1] - 1
    else:
        context_start = 0
        context_end = len(input_ids) - 1

    # Đảm bảo index hợp lệ
    context_start = max(0, min(context_start, len(input_ids) - 1))
    context_end = max(context_start, min(context_end, len(input_ids) - 1))

    # 5. Chỉ lấy Logits trong phạm vi của context
    start_logits = outputs.start_logits[0, context_start : context_end + 1]
    end_logits = outputs.end_logits[0, context_start : context_end + 1]
    
    # 6. Tìm các cặp (start, end) tốt nhất bằng PyTorch (Joint Scoring)
    n_best = 20
    best_start_values, best_start_indices = torch.topk(start_logits, min(n_best, len(start_logits)))
    best_end_values, best_end_indices = torch.topk(end_logits, min(n_best, len(end_logits)))
    
    best_start_indices = best_start_indices.tolist()
    best_end_indices = best_end_indices.tolist()
    
    candidates = []
    seen_texts = set()
    
    for start_idx in best_start_indices:
        for end_idx in best_end_indices:
            # Điều kiện: start <= end và độ dài đáp án không quá 100 tokens
            if start_idx <= end_idx and end_idx - start_idx + 1 <= 100:
                score = start_logits[start_idx].item() + end_logits[end_idx].item()
                actual_start = start_idx + context_start
                actual_end = end_idx + context_start
                
                # Decode câu trả lời tương ứng
                tokens = inputs.input_ids[0, actual_start : actual_end + 1]
                ans_text = tokenizer.decode(tokens, skip_special_tokens=True).replace("_", " ").strip()
                
                # Tránh trùng lặp nội dung và bỏ qua câu trả lời rỗng hoặc chỉ toàn dấu câu
                if ans_text and not all(c in ".,!?-_():;\"' " for c in ans_text):
                    if ans_text not in seen_texts:
                        candidates.append({
                            "text": ans_text,
                            "score": score
                        })
                        seen_texts.add(ans_text)
                        
    # Sắp xếp các ứng viên theo điểm số giảm dần
    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
    
    # In ra top 5 ứng viên tốt nhất để phân tích/debug
    print("\n🔍 TOP 5 ĐÁP ÁN ĐƯỢC MÔ HÌNH ĐÁNH GIÁ CAO NHẤT:")
    for idx, cand in enumerate(candidates[:5]):
        print(f"  [{idx+1}] Điểm số: {cand['score']:.4f} | Đáp án: {cand['text']}")
    print("-" * 50)
    
    if not candidates:
        return "Không tìm thấy câu trả lời trong văn bản."
        
    return candidates[0]["text"]




def main():
    model, tokenizer, device = load_qa_model()
    
    default_context = (
        "Việt Nam có một nền văn hoá đặc sắc, lâu đời gắn liền với lịch sử hình thành và phát triển của dân tộc.\n\n"
        "Các nhà sử học thống nhất ý kiến ở một điểm: Việt Nam có một cộng đồng văn hoá khá rộng lớn được hình thành "
        "vào khoảng nửa đầu thiên niên kỉ thứ nhất trước Công nguyên và phát triển rực rỡ vào giữa thiên niên kỉ này. "
        "Đó là cộng đồng văn hoá Đông Sơn. Cộng đồng văn hoá ấy phát triển cao so với các nền văn hoá khác đương thời "
        "trong khu vực, có những nét độc đáo riêng nhưng vẫn mang nhiều điểm đặc trưng của văn hoá vùng Đông Nam Á, "
        "vì có chung chủng gốc Nam Á (Mongoloid phương Nam) và nền văn minh lúa nước. Những con đường phát triển khác "
        "nhau của văn hoá bản địa tại các khu vực khác nhau (lưu vực sông Hồng, sông Mã, sông Cả v.v...) đã hội tụ với "
        "nhau, hợp thành văn hoá Đông Sơn. Đây cũng là thời kỳ ra đời nhà nước \"phôi thai\" đầu tiên của Việt Nam dưới "
        "hình thức cộng đồng liên làng và siêu làng (để chống giặc và đắp giữ đê trồng lúa), từ đó các bộ lạc nguyên thuỷ "
        "phát triển thành dân tộc."
    )
    
    default_question = "Các nhà sử học thống nhất ý kiến ở điểm nào?"
    
    print("\n📝 VĂN BẢN MẪU:")
    print("-" * 60)
    print(default_context)
    print("-" * 60)
    print(f"CÂU HỎI MẪU: {default_question}")
    
    # Hỏi câu hỏi mặc định trước
    print("\n🤖 Đang phân tích và trả lời câu hỏi mẫu...")
    ans = answer_question(model, tokenizer, device, default_context, default_question)
    print(f"👉 Câu trả lời: {ans}\n")
    
    # Vòng lặp cho phép người dùng dán văn bản và đặt câu hỏi
    print("=" * 60)
    print("CHẾ ĐỘ TỰ NHẬP VĂN BẢN ĐỂ KIỂM THỬ (QA INTERACTIVE)")
    print("=" * 60)
    
    try:
        # Lấy context từ người dùng
        print("\n📥 Hãy dán (paste) văn bản Context của bạn vào đây (Nhấn Enter -> gõ 'DONE' rồi Enter để kết thúc nhập):")
        context_lines = []
        while True:
            line = input()
            if line.strip() == "DONE":
                break
            context_lines.append(line)
        
        user_context = "\n".join(context_lines).strip()
        if not user_context:
            print("⚠️ Văn bản rỗng. Sử dụng văn bản mẫu mặc định.")
            user_context = default_context
            
        print("\n✅ Đã nhận văn bản!")
        
        # Nhập câu hỏi liên tục
        while True:
            user_question = input("\n❓ Nhập câu hỏi của bạn (hoặc gõ 'exit' để thoát): ").strip()
            if not user_question:
                continue
            if user_question.lower() in ["exit", "quit", "q"]:
                print("👋 Tạm biệt!")
                break
                
            print("⏳ Đang xử lý câu hỏi...")
            answer = answer_question(model, tokenizer, device, user_context, user_question)
            
            print("\n" + "*" * 50)
            print(f"Hỏi: {user_question}")
            print(f"Đáp: {answer}")
            print("*" * 50)
            
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Đã thoát chương trình kiểm thử.")

if __name__ == "__main__":
    main()
