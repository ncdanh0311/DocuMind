import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, GenerationConfig
from peft import PeftModel
from pyvi import ViTokenizer

class SummarizationService:
    def __init__(self):
        self.cache_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../hf_cache"
        ))
        
        # Đường dẫn tuyệt đối đến các thư mục model cục bộ
        self.model_paths = {
            "vit5": os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../results/models/vit5_summarization/best"
            )),
            "bartpho": os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../results/models/bartpho_summarization/checkpoint-3750"
            ))
        }
        
        # Tên các base model tương ứng từ Hugging Face
        self.base_model_names = {
            "vit5": "VietAI/vit5-base",
            "bartpho": "vinai/bartpho-word-base"
        }
        
        # Quản lý cache riêng biệt cho từng mô hình
        self.models = {"vit5": None, "bartpho": None}
        self.tokenizers = {"vit5": None, "bartpho": None}
        self.devices = {"vit5": None, "bartpho": None}

    def _ensure_loaded(self, model_type: str = "vit5"):
        """
        Tải mô hình tóm tắt và adapters LoRA lên bộ nhớ (Lazy Loading) khi có yêu cầu đầu tiên.
        """
        if model_type not in self.models:
            model_type = "vit5"
            
        if self.models[model_type] is not None:
            return

        model_path = self.model_paths[model_type]
        print(f"Đang tải mô hình tóm tắt {model_type} từ: {model_path}...")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy mô hình tóm tắt {model_type} tại: {model_path}")

        # Tối ưu thiết bị chạy: MPS (Apple Silicon GPU) -> CUDA -> CPU
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")

        print(f"💻 Load {model_type} Summarization trên thiết bị: {device}")

        # 1. Load Tokenizer
        if model_type == "vit5":
            # Load tokenizer từ model_path cục bộ để tránh lỗi không tương thích sentencepiece
            self.tokenizers[model_type] = AutoTokenizer.from_pretrained(
                model_path,
                use_fast=False
            )
        else: # bartpho
            # BARTpho-word sử dụng BPE tokenizer cấp độ từ từ base model
            self.tokenizers[model_type] = AutoTokenizer.from_pretrained(
                self.base_model_names[model_type],
                cache_dir=self.cache_dir,
                use_fast=False
            )

        if self.tokenizers[model_type].pad_token is None:
            self.tokenizers[model_type].pad_token = self.tokenizers[model_type].eos_token

        # 2. Load base Seq2Seq model
        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            self.base_model_names[model_type],
            cache_dir=self.cache_dir,
            torch_dtype=torch.float32,
            attn_implementation="eager"
        )

        # 3. Load LoRA adapter và merge
        print(f"Đang nạp adapters LoRA {model_type} từ: {model_path}...")
        model = PeftModel.from_pretrained(base_model, model_path)
        self.models[model_type] = model.merge_and_unload()
        self.models[model_type].eval()
        self.models[model_type] = self.models[model_type].to(device)
        self.devices[model_type] = device

        # 4. Thiết lập Generation Config mặc định theo bảng thông số chuẩn
        gen_config = GenerationConfig()
        gen_config.max_length = 256
        gen_config.min_length = 30
        gen_config.num_beams = 4
        gen_config.length_penalty = 1.2
        gen_config.no_repeat_ngram_size = 3
        gen_config.do_sample = False
        gen_config.early_stopping = True
        gen_config.pad_token_id = self.tokenizers[model_type].pad_token_id
        gen_config.eos_token_id = self.tokenizers[model_type].eos_token_id
        
        if model_type == "vit5":
            gen_config.decoder_start_token_id = self.tokenizers[model_type].pad_token_id
        else:
            gen_config.decoder_start_token_id = self.tokenizers[model_type].eos_token_id

        self.models[model_type].generation_config = gen_config
        print(f"✅ {model_type} Summarization model đã sẵn sàng!")

    def summarize(self, text: str, model_type: str = "vit5") -> str:
        """
        Thực hiện tóm tắt văn bản bằng mô hình ViT5 hoặc BARTpho kết hợp LoRA.
        """
        if not text or not text.strip():
            return ""

        if model_type not in self.models:
            model_type = "vit5"

        self._ensure_loaded(model_type)
        tokenizer = self.tokenizers[model_type]
        model = self.models[model_type]
        device = self.devices[model_type]

        # Dọn dẹp khoảng trắng thừa
        text = " ".join(text.split())

        # VnCoreNLP / PyVi wseg pre-step bắt buộc cho BARTpho-word
        if model_type == "bartpho":
            segmented_text = ViTokenizer.tokenize(text)
            input_text = "summarize: " + segmented_text
        else: # vit5
            input_text = "summarize: " + text

        # Tokenize văn bản đầu vào (Giới hạn tối đa 512 token theo đúng báo cáo)
        inputs = tokenizer(
            input_text,
            max_length=512,
            truncation=True,
            return_tensors="pt"
        ).to(device)

        # Xóa token_type_ids để tránh lỗi Seq2Seq
        inputs.pop("token_type_ids", None)

        # Sinh tóm tắt
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=256,
                min_length=30,
                num_beams=4,
                length_penalty=1.2,
                no_repeat_ngram_size=3,
                do_sample=False,
                early_stopping=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        # Giải mã và làm sạch kết quả
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
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
