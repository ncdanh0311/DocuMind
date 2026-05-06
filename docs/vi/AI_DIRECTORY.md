# 📂 Hướng dẫn Thư mục AI - DocuMind

<div align="right">
  🌍 <b><a href="../en/AI_DIRECTORY.md">English Version</a></b>
</div>

Thư mục `ai/` là trung tâm nghiên cứu và phát triển cốt lõi của DocuMind. Nơi đây chứa tất cả mọi thứ liên quan đến huấn luyện mô hình, đánh giá, tập dữ liệu và quản lý các thí nghiệm.

---

## 🏗️ Cấu trúc Thư mục

| Thư mục/Tập tin | Mô tả |
|---|---|
| **`src/`** | Mã nguồn Python cốt lõi cho việc huấn luyện mô hình, tiền xử lý dữ liệu và logic đánh giá. |
| **`scripts/`** | Các shell script (`.sh`) và script tiện ích để tự động hóa quá trình huấn luyện và xử lý hàng loạt. |
| **`configs/`** | Các tập tin cấu hình (YAML/JSON) chứa siêu tham số (hyperparameters), đường dẫn mô hình và thiết lập tập dữ liệu. |
| **`datasets/`** | Tập dữ liệu huấn luyện, kiểm thử và đánh giá (CSV, JSON hoặc văn bản thô). |
| **`results/`** | Các mô hình đã huấn luyện hoàn chỉnh, nhật ký đánh giá và các chỉ số hiệu năng. |
| **`checkpoints/`** | Các trọng số mô hình trung gian được lưu trong quá trình huấn luyện để có thể khôi phục khi gặp lỗi. |
| **`hf_cache/`** | Bộ nhớ đệm cục bộ cho các mô hình và tokenizer từ HuggingFace để tránh tải xuống lặp lại. |
| **`README.md`** | Hướng dẫn cụ thể cho thành phần nghiên cứu AI. |

---

## ⚙️ Quy trình làm việc AI (Workflow)

Quy trình làm việc điển hình trong thư mục này tuân theo các giai đoạn sau:

1.  **Chuẩn bị dữ liệu (`datasets/`):** Dữ liệu thô được thu thập và tiền xử lý bằng các script trong `src/`.
2.  **Cấu hình (`configs/`):** Các tham số huấn luyện (learning rate, batch size, epochs) được xác định.
3.  **Huấn luyện (`src/` & `scripts/`):** Các mô hình (ViT5, BARTpho, v.v.) được huấn luyện, tiến trình được lưu vào `checkpoints/`.
4.  **Đánh giá (`results/`):** Các mô hình cuối cùng được đánh giá trên tập kiểm thử và tạo ra nhật ký (logs).
5.  **Triển khai:** Các mô hình thành công từ `results/models/` sẽ được tích hợp vào `backend/` để sử dụng thực tế.

---

## 📊 Thí nghiệm & Nhật ký (Logs)

Tất cả nhật ký huấn luyện và chỉ số (Loss, Accuracy, ROUGE scores, F1) được lưu trữ trong `ai/results/logs/`. Những nhật ký này cực kỳ quan trọng để so sánh hiệu năng của các kiến trúc khác nhau (ví dụ: so sánh BARTpho vs. ViT5 cho tác vụ tóm tắt).

---
