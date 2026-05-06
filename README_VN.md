<p align="center">
  <a href="https://huit.edu.vn/" title="Trường Đại học Công Thương TP.HCM">
    <img src="./assets/Logo%20HUIT-03.png" alt="Ho Chi Minh City University of Industry and Trade (HUIT)" width="400">
  </a>
</p>

<h1 align="center"><b>ĐỒ ÁN CUỐI KỲ DEEP LEARNING - DOCUMIND</b></h1>

<p align="center">
  <img src="https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white" alt="Flutter" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</p>

<div align="center">
  <p>🌍 <b><a href="./README.md">English Version</a></b></p>
</div>

<div align="center">

<!-- HEADER BANNER -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00B4D8,100:0077B6&height=220&section=header&text=Doan%20Tan%20Minh%20Tan&fontSize=50&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=AI%20Engineer%20%7C%20Fullstack%20Engineer&descSize=20&descAlignY=55&descAlign=50" width="100%"/>

<br/>

[![Portfolio](https://img.shields.io/badge/Portfolio-667eea?style=for-the-badge&logo=vercel&logoColor=white)](#)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/tandoanminh/)
[![Email](https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:doanminhtan.dev@gmail.com)
[![Facebook](https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](#)

<br/>

</div>

<p align="center">
  <img src="./assets/thumbnail.png" alt="Project thumbnail" width="600">
</p>

## Demo Sản Phẩm

<table align="center">
  <tr>
    <td align="center"><img src="./assets/onboarding.png" width="200px"/><br/><b>Giới thiệu</b></td>
    <td align="center"><img src="./assets/login.png" width="200px"/><br/><b>Đăng nhập</b></td>
    <td align="center"><img src="./assets/register.png" width="200px"/><br/><b>Đăng ký</b></td>
  </tr>
  <tr>
    <td align="center"><img src="./assets/home.png" width="200px"/><br/><b>Trang chủ</b></td>
    <td align="center"><img src="./assets/notebook_list.png" width="200px"/><br/><b>Danh sách vở bài tập</b></td>
    <td align="center"><img src="./assets/notebook_detail.png" width="200px"/><br/><b>Chi tiết vở bài tập</b></td>
  </tr>
  <tr>
    <td align="center"><img src="./assets/ai_chat.png" width="200px"/><br/><b>Chat với AI</b></td>
    <td align="center"><img src="./assets/summary.png" width="200px"/><br/><b>Tóm tắt tài liệu</b></td>
    <td align="center"><img src="./assets/personal.png" width="200px"/><br/><b>Cá nhân</b></td>
  </tr>
</table>

<p align="center"><i>Và nhiều tính năng khác như Cài đặt, Thông báo...</i></p>

---

## Thông tin sinh viên

| MSSV | Họ và tên | GitHub | Email |
|:----------:|------------------|-----------------------------------------|------------------------|
| 2001230791 | Đoàn Tấn Minh Tân | [TanDoan1234](https://github.com/TanDoan1234) | doanminhtan.dev@gmail.com |

---

## Mục tiêu

**DocuMind** là trợ lý sổ tay cá nhân hỗ trợ bởi AI, được thiết kế để giúp sinh viên và nhà nghiên cứu quản lý, tóm tắt và tương tác với tài liệu một cách hiệu quả. Bằng cách tận dụng các kỹ thuật **Deep Learning** tiên tiến và **RAG (Retrieval-Augmented Generation)**, DocuMind cho phép người dùng tải lên tài liệu (PDF, Docx) và đặt câu hỏi trực tiếp trên nội dung đó, đảm bảo câu trả lời chính xác với các trích dẫn rõ ràng, loại bỏ hiện tượng "ảo giác" của AI.

---

## 🧠 Công nghệ AI & Deep Learning

Dự án áp dụng các kỹ thuật Deep Learning tiên tiến nhất để tối ưu hóa việc xử lý tài liệu tiếng Việt:

- **Xử lý tài liệu:** Sử dụng [IBM Docling](https://github.com/DS4SD/docling) để phân tích bố cục (Layout Analysis) và trích xuất Markdown từ tài liệu phức tạp (PDF, Docx, Pptx).
- **Text Embedding:** Sử dụng model [Vietnamese-SBERT](https://huggingface.co/keepitreal/vietnamese-sbert) (768 dims) để chuyển đổi văn bản sang vector ngữ nghĩa, hỗ trợ tìm kiếm RAG chính xác.
- **Mô hình ngôn ngữ lớn (LLM):** 
  - **Tóm tắt văn bản:** Đánh giá và sử dụng cả [BARTpho](https://huggingface.co/vinai/bartpho-word) và [ViT5](https://huggingface.co/VietAI/vit5-base) để đạt hiệu quả tối ưu.
  - **Hỏi đáp AI:** Triển khai so sánh giữa [PhoBERT](https://huggingface.co/vinai/phobert-base) và [XLM-RoBERTa](https://huggingface.co/facebook/xlm-roberta-base) cho việc trích xuất câu trả lời theo ngữ cảnh.

---

## 📂 Cấu trúc thư mục

```text
DocuMind/
├── mobile/                      ← Ứng dụng di động Flutter
├── backend/                     
│   ├── processor/               ← Pipeline AI (Docling, Embedding, Summarizer)
│   └── main.py                  ← Entry point của FastAPI
├── tests/                       ← Các script kiểm thử Backend & AI
├── ai/                          ← Model đã huấn luyện và kết quả
├── assets/                      ← Tài nguyên dự án (logo, ảnh demo)
├── pyproject.toml               ← Quản lý thư viện (uv)
└── README_VN.md                 ← Tổng quan dự án (Tiếng Việt)
```

---

## 🛠️ Cài đặt Phát triển

Dự án sử dụng **`uv`** để quản lý môi trường và thư viện Python một cách nhanh chóng và đồng bộ.

### Yêu cầu tiên quyết
- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Flutter SDK (cho mobile)

### Thiết lập & Kiểm thử Backend
1. Cài đặt các thư viện và khởi tạo môi trường:
   ```bash
   uv sync
   ```
2. Chạy các bài kiểm tra AI (Tự động tải model trong lần đầu):
   - **Xử lý tài liệu:** `uv run python tests/test_docling_processor.py`
   - **So sánh ngữ nghĩa:** `uv run python tests/test_embedding_service.py`
   - **Tóm tắt văn bản:** `uv run python tests/test_summarization.py`
   - **Hỏi đáp AI:** `uv run python tests/test_qa.py`

3. Chạy server chính:
   ```bash
   uv run python backend/main.py
   ```

### Thiết lập Mobile
1. Chạy ứng dụng:
   ```bash
   cd mobile
   flutter run
   ```

---

## 📚 Tài liệu Hướng dẫn

Bạn có thể tìm thấy các tài liệu hướng dẫn kỹ thuật chi tiết trong thư mục `docs/`:

- **[Hướng dẫn các Mô hình AI](./docs/vi/AI_MODELS_GUIDE.md)**: Chi tiết về BARTpho, ViT5, PhoBERT, và nhiều hơn nữa.
- **[Hướng dẫn Thư mục AI](./docs/vi/AI_DIRECTORY_GUIDE.md)**: Hiểu về cấu trúc thư mục `ai/` và quy trình nghiên cứu.
- **[Kiến trúc Hệ thống](./docs/en/ARCHITECTURE.md)**: Phân tích sâu về RAG pipeline và thiết kế hệ thống (Bản tiếng Anh).

---
