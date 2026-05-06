# 🧠 Hướng dẫn các Mô hình AI - DocuMind

<div align="right">
  🌍 <b><a href="../en/AI_MODELS.md">English Version</a></b>
</div>

DocuMind sử dụng một bộ sưu tập các mô hình Deep Learning tiên tiến nhất, được tối ưu hóa đặc biệt cho tiếng Việt. Tài liệu này cung cấp chi tiết kỹ thuật về các mô hình được sử dụng cho các tác vụ tóm tắt, hỏi đáp và xử lý tài liệu.

---

## 📋 Tổng quan về các Mô hình

Dự án đánh giá và triển khai hai tác vụ chính sử dụng bốn kiến trúc mô hình khác nhau để so sánh hiệu suất và độ chính xác.

| Tác vụ | Mô hình sử dụng | Kiến trúc |
|:---:|---|---|
| **Tóm tắt văn bản** | BARTpho, ViT5 | Encoder-Decoder (Seq2Seq) |
| **Hỏi đáp (QA)** | PhoBERT, XLM-RoBERTa | Encoder-only |
| **Xử lý tài liệu** | Docling (IBM) | Phân tích bố cục hỗn hợp |

---

## 📝 1. Các mô hình Tóm tắt (Summarization)

Chúng tôi sử dụng hai mô hình Sequence-to-Sequence mạnh mẽ để tạo ra các bản tóm tắt súc tích cho các tài liệu dài.

### **BARTpho** (`bartpho_summarization`)
- **Mô hình gốc:** `vinai/bartpho-word`
- **Mô tả:** Mô hình sequence-to-sequence tiền huấn luyện đầu tiên cho tiếng Việt. Nó đặc biệt mạnh trong việc nắm bắt các phụ thuộc xa và tạo ra các câu tiếng Việt tự nhiên.
- **Cách dùng:** Tạo ra các bản tóm tắt trừu tượng (abstractive) chất lượng cao.

### **ViT5** (`vit5_summarization`)
- **Mô hình gốc:** `VietAI/vit5-base`
- **Mô tả:** Một mô hình dựa trên T5 được tiền huấn luyện trên kho ngữ liệu tiếng Việt khổng lồ. Nó tuân theo triết lý "Text-to-Text Transfer Transformer".
- **Cách dùng:** Xuất sắc trong việc hiểu cấu trúc tài liệu phức tạp và trích lọc thông tin chính.

---

## ❓ 2. Các mô hình Hỏi đáp (Question Answering)

Các mô hình này được sử dụng để trích xuất câu trả lời từ nội dung tài liệu dựa trên câu hỏi của người dùng.

### **PhoBERT** (`phobert_qa`)
- **Mô hình gốc:** `vinai/phobert-base`
- **Mô tả:** Mô hình ngôn ngữ hàng đầu cho tiếng Việt dựa trên kiến trúc RoBERTa. Nó hiểu rất rõ các sắc thái ngữ pháp và từ vựng tiếng Việt.
- **Cách dùng:** Được sử dụng để trích xuất sự kiện chính xác và hiểu ngữ cảnh sâu.

### **XLM-RoBERTa** (`xlmroberta_qa`)
- **Mô hình gốc:** `xlm-roberta-base`
- **Mô tả:** Một mô hình đa ngôn ngữ được huấn luyện trên 100 ngôn ngữ, bao gồm cả tiếng Việt.
- **Cách dùng:** Cung cấp một tiêu chuẩn mạnh mẽ cho việc hiểu đa ngôn ngữ và hoạt động ổn định trên nhiều phong cách tài liệu khác nhau.

---

## 🔍 3. Các Pipeline hỗ trợ

### **Docling (của IBM)**
- **Vai trò:** Tiếp nhận tài liệu (Document Ingestion).
- **Chức năng:** Khác với các bộ thư viện đọc PDF truyền thống, Docling thực hiện phân tích bố cục để xác định tiêu đề, bảng biểu và hình ảnh, chuyển đổi chúng thành Markdown sạch. Điều này giúp AI không bị nhầm lẫn bởi các thông tin ở đầu trang/chân trang hoặc cấu trúc bảng phức tạp.


---

## 🚀 Cách sử dụng trong Backend

Backend được thiết kế để linh hoạt với các mô hình. Bạn có thể chuyển đổi giữa các mô hình này trong cấu hình để so sánh kết quả.

```python
# Ví dụ chuyển đổi mô hình tóm tắt
processor = Summarizer(model_path="ai/results/models/vit5_summarization")
# hoặc
processor = Summarizer(model_path="ai/results/models/bartpho_summarization")
```

---

## 📊 Kết quả Đánh giá
*Kết quả benchmark chi tiết (điểm ROUGE cho tóm tắt, F1/EM cho hỏi đáp) có thể được tìm thấy trong thư mục `ai/results/logs`.*
