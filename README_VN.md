<div align="center">
<h1>
  <img src="./assets/logo.png" alt="DocuMind Logo" width="250" /><br>
  DOCUMIND
</h1>

### Đồ Án Cuối Kỳ Deep Learning
**IBM Docling • BARTpho & ViT5 • PhoBERT & XLM-RoBERTa • Sentence Transformers**

---

[![Flutter](https://img.shields.io/badge/Flutter-3.24+-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-4fb320?style=for-the-badge)](LICENSE)
[![Nền tảng](https://img.shields.io/badge/Nền%20tảng-iOS%20|%20Android%20|%20Web-9944FF?style=for-the-badge)](#)
[![Stars](https://img.shields.io/badge/Stars-21-ffcc33?style=for-the-badge&logo=github&logoColor=white)](#)

<br/>

[![Portfolio](https://img.shields.io/badge/Portfolio-667eea?style=for-the-badge&logo=vercel&logoColor=white)](#)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/tandoanminh/)
[![Email](https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](#)
[![Facebook](https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](#)

<br/>

> *DocuMind là trợ lý sổ tay cá nhân AI được thiết kế để giúp sinh viên và nhà nghiên cứu quản lý và tóm tắt tài liệu hiệu quả bằng các mô hình Deep Learning tiên tiến nhất.*

<br/>

[**Bắt đầu**](#cài-đặt-phát-triển) · [**Công nghệ AI**](#công-nghệ-ai--deep-learning) · [**Tính năng**](#demo-sản-phẩm) · [**Tài liệu**](#tài-liệu-hướng-dẫn)
</div>

<div align="center">
  🌍 <b><a href="./README.md">English Version</a></b>
</div>

---

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

<p align="center">
  <a href="https://huit.edu.vn/">
    <img src="./assets/Logo%20HUIT-03.png" alt="HUIT Logo" width="450">
  </a>
</p>

| MSSV | Họ và tên | GitHub | Email |
|:----------:|------------------|-----------------------------------------|------------------------|
| 2001230791 | Đoàn Tấn Minh Tân | [TanDoan1234](https://github.com/TanDoan1234) | doanminhtan.dev@gmail.com |

---

## Mục tiêu

**DocuMind** là trợ lý sổ tay cá nhân hỗ trợ bởi AI, được thiết kế để giúp sinh viên và nhà nghiên cứu quản lý và tóm tắt tài liệu một cách hiệu quả. Bằng cách tận dụng các kỹ thuật **Deep Learning** tiên tiến, DocuMind cho phép người dùng tải lên tài liệu (PDF, Docx) và nhận lại các bản tóm tắt chất lượng cao cùng các phân tích chuyên sâu, đảm bảo quá trình xử lý thông tin chính xác.

---

## 🧠 Công nghệ AI & Deep Learning

Dự án áp dụng các kỹ thuật Deep Learning tiên tiến nhất để tối ưu hóa việc xử lý tài liệu tiếng Việt:

- **Xử lý tài liệu:** Sử dụng [IBM Docling](https://github.com/DS4SD/docling) để phân tích bố cục (Layout Analysis) và trích xuất Markdown từ tài liệu phức tạp (PDF, Docx, Pptx).
- **Mô hình ngôn ngữ lớn (LLM):** 
  - **Tóm tắt văn bản:** Đánh giá và sử dụng cả [BARTpho](https://huggingface.co/vinai/bartpho-word) và [ViT5](https://huggingface.co/VietAI/vit5-base) để đạt hiệu quả tối ưu.
  - **Hỏi đáp AI:** Triển khai so sánh giữa [PhoBERT](https://huggingface.co/vinai/phobert-base) và [XLM-RoBERTa](https://huggingface.co/facebook/xlm-roberta-base) cho việc trích xuất câu trả lời theo ngữ cảnh.

---

## 📂 Cấu trúc thư mục

```text
DocuMind/
├── mobile/                      ← Ứng dụng di động Flutter
├── backend/                     
│   ├── app/                     ← Logic ứng dụng (API, Core, Models)
│   ├── processor/               ← Pipeline AI (Docling, Embedding, Summarizer)
│   ├── main.py                  ← Điểm khởi đầu FastAPI
│   └── Dockerfile               ← Định nghĩa container Backend
├── docs/                        ← Tài liệu hướng dẫn cài đặt
├── tests/                       ← Các script kiểm thử Backend & AI
├── ai/                          ← Các mô hình đã huấn luyện
├── assets/                      ← Tài nguyên dự án (logo, ảnh demo)
├── docker-compose.yml           ← Điều phối dịch vụ (Backend & DB)
├── pyproject.toml               ← Quản lý thư viện (uv)
└── .env                         ← Biến môi trường (DB, Keys)
```

---

## 🛠️ Cài đặt Phát triển

Chúng tôi cung cấp hai cách để thiết lập môi trường phát triển cho DocuMind. Hãy chọn cách phù hợp nhất với quy trình của bạn:

*   🚀 **[Hướng dẫn chạy bằng Docker (Khuyên dùng)](./docs/docker_setup_vn.md)**: Khởi chạy dự án chỉ trong vài phút với môi trường đã đóng gói sẵn (Backend + Database).
*   🔧 **[Hướng dẫn chạy Local](./docs/local_setup_vn.md)**: Cài đặt thủ công cho những ai muốn chạy các dịch vụ trực tiếp trên máy.

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

### Bắt đầu nhanh
- 📖 **[Giới thiệu](./docs/vi/INSTALLATION.md#introduction)** - Tìm hiểu về những gì DocuMind cung cấp.
- ⚡ **[Bắt đầu nhanh](./docs/vi/INSTALLATION.md#quick-start)** - Khởi chạy dự án trong 5 phút.
- 🔧 **[Cài đặt](./docs/vi/INSTALLATION.md#installation)** - Hướng dẫn thiết lập toàn diện.

### Hướng dẫn sử dụng
- 📱 **[Tổng quan giao diện](./docs/vi/FEATURES.md#interface-overview)** - Hiểu về bố cục ứng dụng.
- 📚 **[Vở bài tập](./docs/vi/FEATURES.md#notebooks)** - Cách tổ chức nghiên cứu của bạn.
- ✍️ **[Tóm tắt tài liệu](./docs/vi/FEATURES.md#summarization)** - Các tính năng tóm tắt tự động.
- 💬 **[AI Chat](./docs/vi/FEATURES.md#chat)** - Trò chuyện AI với tài liệu của bạn.

### Chủ đề nâng cao
- ⚙️ **[Quy trình xử lý](./docs/vi/DOCUMENT_PROCESSOR.md)** - Phân tích kỹ thuật sâu về quy trình xử lý tài liệu.
- 🤖 **[Mô hình AI](./docs/vi/AI_MODELS.md)** - Cấu hình và chi tiết về các model AI.
- 📂 **[Hướng dẫn thư mục AI](./docs/vi/AI_DIRECTORY.md)** - Hiểu về thư mục nghiên cứu AI.
- 🚀 **[Triển khai](./docs/vi/DOCUMENT_PROCESSOR.md#deployment)** - Hướng dẫn triển khai hệ thống.

---
