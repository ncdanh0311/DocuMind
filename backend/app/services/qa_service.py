import os
import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from pyvi import ViTokenizer

class QAService:
    def __init__(self):
        self.model_name = "phobert_qa"
        self.model_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../../../ai/results/models/phobert_qa/best_model"
        ))
        self.model = None
        self.tokenizer = None
        self.device = None

    def _ensure_loaded(self):
        """
        Tải mô hình lên bộ nhớ một lần duy nhất khi có yêu cầu đầu tiên (Lazy Loading).
        Điều này tránh làm chậm quá trình khởi động lại của Backend (Hot Reload).
        """
        if self.model is not None:
            return

        print(f"Đang tải mô hình PhoBERT QA từ: {self.model_path}...")
        if not os.path.exists(self.model_path):
            # Nếu không có model finetune, ta fallback về model mặc định trên HF Hub
            print("Thư mục model finetune cục bộ không tồn tại. Đang fallback về mô hình mặc định...")
            # Sử dụng model QA tương ứng hoặc ném ra exception nếu bắt buộc phải có
            raise FileNotFoundError(f"Không tìm thấy mô hình PhoBERT QA tại: {self.model_path}")

        # Tối ưu thiết bị chạy: MPS (Apple Silicon GPU) -> CUDA -> CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        print(f"💻 Load PhoBERT QA trên thiết bị: {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForQuestionAnswering.from_pretrained(self.model_path).to(self.device)

    def answer_question(self, context: str, question: str) -> str:
        """
        Thực hiện hỏi đáp trích xuất thông tin sử dụng mô hình PhoBERT QA.
        """
        if not context or not question:
            return "Văn bản hoặc câu hỏi không hợp lệ."

        self._ensure_loaded()

        # 1. Tách từ tiếng Việt bằng ViTokenizer
        segmented_context = ViTokenizer.tokenize(context)
        segmented_question = ViTokenizer.tokenize(question)

        # 2. Tokenize dữ liệu đầu vào
        inputs = self.tokenizer(
            segmented_question,
            segmented_context,
            return_tensors="pt",
            truncation=True,
            max_length=258  # Giới hạn max_position_embeddings của PhoBERT QA
        ).to(self.device)

        # 3. Chạy model dự báo
        with torch.no_grad():
            outputs = self.model(**inputs)

        # 4. Tìm các token EOS (2) để định vị context
        input_ids = inputs.input_ids[0].tolist()
        eos_token_id = self.tokenizer.eos_token_id if self.tokenizer.eos_token_id is not None else 2
        eos_indices = [i for i, token_id in enumerate(input_ids) if token_id == eos_token_id]

        if len(eos_indices) >= 2:
            context_start = eos_indices[1] + 1
            context_end = eos_indices[-1] - 1
        else:
            context_start = 0
            context_end = len(input_ids) - 1

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
                if start_idx <= end_idx and end_idx - start_idx + 1 <= 100:
                    score = start_logits[start_idx].item() + end_logits[end_idx].item()
                    actual_start = start_idx + context_start
                    actual_end = end_idx + context_start

                    tokens = inputs.input_ids[0, actual_start : actual_end + 1]
                    ans_text = self.tokenizer.decode(tokens, skip_special_tokens=True).replace("_", " ").strip()

                    # Lọc bỏ câu trả lời rỗng hoặc toàn dấu câu
                    if ans_text and not all(c in ".,!?-_():;\"' " for c in ans_text):
                        if ans_text not in seen_texts:
                            candidates.append({
                                "text": ans_text,
                                "score": score
                            })
                            seen_texts.add(ans_text)

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

        if not candidates:
            return "Không tìm thấy câu trả lời trong văn bản."

        return candidates[0]["text"]

# Singleton instance
qa_service = QAService()
