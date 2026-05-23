import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List

class EmbeddingService:
    def __init__(self):
        self.model_name = "intfloat/multilingual-e5-small"
        
        # Lựa chọn thiết bị chạy tối ưu: MPS (Apple Silicon) -> CUDA -> CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
            
        print(f"Loading Embedding Model '{self.model_name}' on device: {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)

    def _average_pool(self, last_hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask.unsqueeze(-1).bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1, keepdim=True)

    def embed_text(self, texts: List[str], is_query: bool = False) -> List[List[float]]:
        """
        Sinh vector embedding cho danh sách các chuỗi văn bản.
        
        Args:
            texts: Danh sách các văn bản cần sinh vector.
            is_query: Đặt thành True nếu là câu hỏi tìm kiếm (query), 
                      False nếu là tài liệu lưu trữ (passage).
        """
        if not texts:
            return []

        # Thêm tiền tố đặc thù của E5: "query: " hoặc "passage: "
        prefix = "query: " if is_query else "passage: "
        prefixed_texts = [f"{prefix}{t}" for t in texts]

        # Tokenize văn bản và chuyển lên thiết bị tương ứng
        inputs = self.tokenizer(
            prefixed_texts, 
            max_length=512, 
            padding=True, 
            truncation=True, 
            return_tensors='pt'
        ).to(self.device)
        
        # Sinh vector embedding
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = self._average_pool(outputs.last_hidden_state, inputs['attention_mask'])
            
            # Chuẩn hóa L2 (L2 normalization) để tối ưu cho phép đo khoảng cách cosine
            embeddings = F.normalize(embeddings, p=2, dim=1)
            
        return embeddings.cpu().tolist()

# Singleton instance
embedding_service = EmbeddingService()
