import evaluate
import numpy as np
import torch

class SumMetrics:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.rouge_scorer = evaluate.load("rouge")

    def compute(self, eval_pred):
        predictions, labels = eval_pred
        
        # 1. Xu ly predictions (du doan tu mo hinh)
        if isinstance(predictions, tuple):
            predictions = predictions[0]
            
        # Chuyen ve CPU va ep kieu int32 de tranh loi Overflow tren Linux
        if isinstance(predictions, torch.Tensor):
            predictions = predictions.cpu().numpy()
        predictions = np.array(predictions).astype(np.int32)
            
        # Giai ma chuoi token thanh van ban
        decoded_preds = self.tokenizer.batch_decode(predictions, skip_special_tokens=True)
        
        # 2. Xu ly labels (dap an chuan)
        # Thay the -100 bang pad_token de decode
        labels = np.where(labels != -100, labels, self.tokenizer.pad_token_id)
        if isinstance(labels, torch.Tensor):
            labels = labels.cpu().numpy()
        labels = labels.astype(np.int32)
        
        decoded_labels = self.tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        # 3. Hau xu ly cho tieng Viet (Xoa dau gach duoi de tinh diem chuan)
        decoded_preds = [text.replace("_", " ") for text in decoded_preds]
        decoded_labels = [text.replace("_", " ") for text in decoded_labels]
        
        # 4. Tinh toan ROUGE
        result = self.rouge_scorer.compute(
            predictions=decoded_preds, 
            references=decoded_labels, 
            use_stemmer=True
        )
        
        # Lam tron ket qua
        return {k: round(v, 4) for k, v in result.items()}