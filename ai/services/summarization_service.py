import os
import torch
from transformers import T5Tokenizer, AutoModelForSeq2SeqLM, GenerationConfig
from peft import PeftModel

class SummarizationService:
    def __init__(self):
        self.model_name = "vit5_summarization"
        # Đường dẫn tuyệt đối đến thư mục model cục bộ
        self.model_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../results/models/vit5_summarization/best"
        ))
        self.base_model_name = "VietAI/vit5-base"
        self.cache_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../hf_cache"
        ))
        self.model = None
        self.tokenizer = None
        self.device = None

    def _ensure_loaded(self):
        """
        Tải mô hình ViT5 và adapters LoRA lên bộ nhớ (Lazy Loading) khi có yêu cầu đầu tiên.
        """
        if self.model is not None:
            return

        print(f"Đang tải mô hình ViT5 từ: {self.model_path}...")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Không tìm thấy mô hình ViT5 tại: {self.model_path}")

        # Tối ưu thiết bị chạy: MPS (Apple Silicon GPU) -> CUDA -> CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        print(f"💻 Load ViT5 Summarization trên thiết bị: {self.device}")

        # 1. Load tokenizer từ model_path cục bộ để tránh lỗi không tương thích sentencepiece
        from transformers import AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            use_fast=False
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # 2. Load base Seq2Seq model
        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            self.base_model_name,
            cache_dir=self.cache_dir,
            torch_dtype=torch.float32,
            attn_implementation="eager"
        )

        # 3. Load LoRA adapter và merge
        print(f"Đang nạp adapters LoRA từ: {self.model_path}...")
        model = PeftModel.from_pretrained(base_model, self.model_path)
        self.model = model.merge_and_unload()
        self.model.eval()
        self.model = self.model.to(self.device)

        # 4. Thiết lập Generation Config mặc định theo bảng thông số chuẩn
        gen_config = GenerationConfig()
        gen_config.max_length = 256
        gen_config.min_length = 30
        gen_config.num_beams = 4
        gen_config.length_penalty = 1.2
        gen_config.no_repeat_ngram_size = 3
        gen_config.do_sample = False
        gen_config.early_stopping = True
        gen_config.pad_token_id = self.tokenizer.pad_token_id
        gen_config.eos_token_id = self.tokenizer.eos_token_id
        gen_config.decoder_start_token_id = self.tokenizer.pad_token_id

        self.model.generation_config = gen_config
        print("✅ ViT5 Summarization model đã sẵn sàng!")

    def summarize(self, text: str) -> str:
        """
        Thực hiện tóm tắt văn bản bằng mô hình ViT5 + LoRA.
        """
        if not text or not text.strip():
            return ""

        self._ensure_loaded()

        # Dọn dẹp khoảng trắng thừa
        text = " ".join(text.split())
        input_text = "summarize: " + text

        # Tokenize văn bản đầu vào
        inputs = self.tokenizer(
            input_text,
            max_length=768,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        # Xóa token_type_ids để tránh lỗi Seq2Seq
        inputs.pop("token_type_ids", None)

        # Sinh tóm tắt
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=256,
                min_length=30,
                num_beams=4,
                length_penalty=1.2,
                no_repeat_ngram_size=3,
                do_sample=False,
                early_stopping=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Giải mã và làm sạch kết quả
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        result = result.replace("_", " ").strip()

        # Loại bỏ các prefix thừa do model tự sinh ra nếu có
        for prefix in ["*rize:", "summarize:", "*rize :", "summarize :"]:
            if result.lower().startswith(prefix):
                result = result[len(prefix):].strip()

        # Loại bỏ dấu hoa thị '*' ở đầu nếu có
        if result.startswith("*"):
            result = result[1:].strip()

        # Gộp các khoảng trắng liên tiếp lại thành 1 khoảng trắng duy nhất
        result = " ".join(result.split())

        # Viết hoa chữ cái đầu tiên
        if result:
            result = result[0].upper() + result[1:]

        return result


# Singleton instance
summarization_service = SummarizationService()
