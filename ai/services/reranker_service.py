import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Any

class RerankerService:
    def __init__(self):
        self.model_name = "namdp-ptit/ViRanker"
        self.cache_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../hf_cache"
        ))
        self.model = None
        self.tokenizer = None
        self.device = None

    def _ensure_loaded(self):
        """
        Tải mô hình ViRanker lên bộ nhớ (Lazy Loading) khi có yêu cầu đầu tiên.
        """
        if self.model is not None:
            return

        print(f"Đang tải mô hình Reranker từ HF: {self.model_name}...")
        
        # Tối ưu thiết bị chạy: MPS (Apple Silicon GPU) -> CUDA -> CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        print(f"Load ViRanker trên thiết bị: {self.device}")

        # Tải tokenizer và model
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir
        ).to(self.device)
        
        self.model.eval()
        print("ViRanker Reranker model đã sẵn sàng!")

    def rerank(self, question: str, passages: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Thực hiện rerank danh sách các đoạn văn bản (passages) dựa trên câu hỏi (question).
        Trả về top_k kết quả tốt nhất kèm score.
        """
        if not question or not passages:
            return []

        self._ensure_loaded()

        # Tạo các cặp [question, passage] để đưa vào cross-encoder
        pairs = [[question, passage] for passage in passages]

        # Tokenize cặp câu
        inputs = self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)

        # Rerank bằng cross-encoder
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Logits biểu thị mức độ liên quan, chuyển sang float32 trên CPU để xử lý tiếp
            scores = outputs.logits.view(-1,).float().cpu().tolist()

        # Ánh xạ kết quả kèm index gốc và score tương ứng
        results = []
        for i, score in enumerate(scores):
            results.append({
                "index": i,
                "text": passages[i],
                "score": float(score)
            })

        # Sắp xếp theo score giảm dần
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        # Trả về top_k kết quả
        return results[:top_k]

# Singleton instance
reranker_service = RerankerService()
