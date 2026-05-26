import os
import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from pyvi import ViTokenizer

class QAService:
    def __init__(self):
        # Đường dẫn tương đối từ ai/services/qa_service.py tới thư mục models
        self.model_paths = {
            "phobert_qa": os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../results/models/phobert_qa/best_model"
            )),
            "xlmroberta_qa": os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../results/models/xlmroberta_qa/best_model"
            ))
        }
        self.cache_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../hf_cache"
        ))
        self.models = {"phobert_qa": None, "xlmroberta_qa": None}
        self.tokenizers = {"phobert_qa": None, "xlmroberta_qa": None}
        self.devices = {"phobert_qa": None, "xlmroberta_qa": None}

    def _ensure_loaded(self, model_type: str):
        """
        Tải mô hình lên bộ nhớ khi có yêu cầu đầu tiên (Lazy Loading).
        """
        if model_type not in self.models:
            model_type = "phobert_qa"

        if self.models[model_type] is not None:
            return

        model_path = self.model_paths[model_type]
        print(f"Đang tải mô hình {model_type} từ: {model_path}...")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy mô hình {model_type} tại: {model_path}")

        # Tối ưu thiết bị chạy: MPS (Apple Silicon GPU) -> CUDA -> CPU
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")

        print(f"💻 Load {model_type} trên thiết bị: {device}")
        self.tokenizers[model_type] = AutoTokenizer.from_pretrained(model_path)
        self.models[model_type] = AutoModelForQuestionAnswering.from_pretrained(model_path).to(device)
        self.devices[model_type] = device

    def answer_question(self, context: str, question: str, model_type: str = "phobert_qa") -> str:
        """
        Thực hiện hỏi đáp trích xuất thông tin sử dụng mô hình PhoBERT QA hoặc XLM-RoBERTa QA.
        Áp dụng kỹ thuật Sliding Window để quét toàn bộ context dài mà không bỏ sót thông tin.
        """
        if not context or not question:
            return "ERR_INVALID_INPUT"

        if model_type not in self.models:
            model_type = "phobert_qa"

        self._ensure_loaded(model_type)

        model = self.models[model_type]
        tokenizer = self.tokenizers[model_type]
        device = self.devices[model_type]

        # Xác định các tham số Sliding Window theo cấu hình mô hình
        if model_type == "phobert_qa":
            max_len = 384
            stride = 96
            # Tách từ tiếng Việt bằng ViTokenizer cho PhoBERT
            segmented_context = ViTokenizer.tokenize(context)
            segmented_question = ViTokenizer.tokenize(question)
        else: # xlmroberta_qa
            max_len = 512
            stride = 128
            # XLM-RoBERTa hoạt động tốt trên raw text không tách từ
            segmented_context = context
            segmented_question = question

        # 2. Tokenize với Sliding Window
        encodings = tokenizer(
            segmented_question,
            segmented_context,
            return_tensors="pt",
            truncation=True,
            max_length=max_len,
            stride=stride,
            return_overflowing_tokens=True,
            padding=True,
        )

        # Loại bỏ overflow_to_sample_mapping (không phải input của model)
        encodings.pop("overflow_to_sample_mapping", None)

        num_windows = encodings.input_ids.shape[0]
        candidates = []
        seen_texts = set()

        # 3. Chạy inference trên từng cửa sổ
        for w in range(num_windows):
            window_inputs = {
                key: val[w : w + 1].to(device)
                for key, val in encodings.items()
            }

            with torch.no_grad():
                outputs = model(**window_inputs)

            # 4. Tìm các token EOS để định vị phạm vi context
            input_ids = window_inputs["input_ids"][0].tolist()
            eos_token_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 2
            eos_indices = [i for i, tid in enumerate(input_ids) if tid == eos_token_id]

            if len(eos_indices) >= 2:
                ctx_start = eos_indices[1] + 1
                ctx_end = eos_indices[-1] - 1
            else:
                ctx_start = 0
                ctx_end = len(input_ids) - 1

            ctx_start = max(0, min(ctx_start, len(input_ids) - 1))
            ctx_end = max(ctx_start, min(ctx_end, len(input_ids) - 1))

            # 5. Chỉ lấy Logits trong phạm vi context
            start_logits = outputs.start_logits[0, ctx_start : ctx_end + 1]
            end_logits = outputs.end_logits[0, ctx_start : ctx_end + 1]

            # 6. Joint Scoring: tìm top N cặp (start, end) tốt nhất
            n_best = 20
            _, best_start_indices = torch.topk(start_logits, min(n_best, len(start_logits)))
            _, best_end_indices = torch.topk(end_logits, min(n_best, len(end_logits)))

            for si in best_start_indices.tolist():
                for ei in best_end_indices.tolist():
                    if si <= ei and ei - si + 1 <= 100:
                        score = start_logits[si].item() + end_logits[ei].item()
                        actual_start = si + ctx_start
                        actual_end = ei + ctx_start

                        tokens = window_inputs["input_ids"][0, actual_start : actual_end + 1]
                        ans_text = tokenizer.decode(tokens, skip_special_tokens=True).replace("_", " ").strip()

                        # Lọc bỏ câu trả lời rỗng hoặc toàn dấu câu
                        if ans_text and not all(c in ".,!?-_():;\"' " for c in ans_text):
                            if ans_text not in seen_texts:
                                candidates.append({
                                    "text": ans_text,
                                    "score": score
                                })
                                seen_texts.add(ans_text)

        # 7. Sắp xếp và trả về câu trả lời có score cao nhất từ tất cả cửa sổ
        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

        if not candidates:
            return "ERR_ANSWER_NOT_FOUND"

        best_candidate = candidates[0]
        # Lọc theo ngưỡng tự tin tối thiểu (THRESHOLD = 1.0) để tránh trích xuất bừa bãi
        # các câu trả lời sai lệch khi người dùng hỏi các câu hỏi chung chung hoặc ngoài phạm vi
        THRESHOLD = 1.0
        if best_candidate["score"] < THRESHOLD:
            print(f"⚠️ Từ chối câu trả lời do điểm tự tin thấp: {best_candidate['score']:.4f} < {THRESHOLD}")
            return "ERR_ANSWER_NOT_FOUND"

        return best_candidate["text"]

# Singleton instance
qa_service = QAService()
