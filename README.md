<div align="center">
  <img src="./assets/logo.png" alt="DocuMind Logo" width="350">
  <h1>DOCUMIND</h1>
  <h3>Deep Learning Final Project</h3>
  <p>IBM Docling • BARTpho & ViT5 • PhoBERT & XLM-RoBERTa • Sentence Transformers</p>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Flutter-3.24+-02569B?style=for-the-badge&logo=flutter&logoColor=white" alt="Flutter" />
  <img src="https://img.shields.io/badge/FastAPI-Latest-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-4fb320?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-iOS%20|%20Android%20|%20Web-9944FF?style=for-the-badge" alt="Platform" />
  <img src="https://img.shields.io/badge/Stars-21-ffcc33?style=for-the-badge&logo=github&logoColor=white" alt="Stars" />
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Portfolio-667eea?style=for-the-badge&logo=vercel&logoColor=white" alt="Portfolio"></a>
  <a href="https://www.linkedin.com/in/tandoanminh/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
  <a href="mailto:doanminhtan.dev@gmail.com"><img src="https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"></a>
  <a href="#"><img src="https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white" alt="Facebook"></a>
</p>

<p align="center">
  <i>DocuMind is an AI-powered personal notebook assistant designed to help students and researchers manage and summarize their documents efficiently using state-of-the-art Deep Learning models.</i>
</p>

<p align="center">
  <a href="#-development-setup"><b>Get Started</b></a> •
  <a href="#-ai--deep-learning-stack"><b>AI Stack</b></a> •
  <a href="#product-demo"><b>Features</b></a> •
  <a href="#-documentation"><b>Docs</b></a>
</p>



<div align="center">


<div align="center">
  <p>🌍 <b><a href="./README_VN.md">Vietnamese Version</a></b></p>
</div>

## Product Demo

<table align="center">
  <tr>
    <td align="center"><img src="./assets/onboarding.png" width="200px"/><br/><b>Onboarding</b></td>
    <td align="center"><img src="./assets/login.png" width="200px"/><br/><b>Login</b></td>
    <td align="center"><img src="./assets/register.png" width="200px"/><br/><b>Register</b></td>
  </tr>
  <tr>
    <td align="center"><img src="./assets/home.png" width="200px"/><br/><b>Home Screen</b></td>
    <td align="center"><img src="./assets/notebook_list.png" width="200px"/><br/><b>Notebook List</b></td>
    <td align="center"><img src="./assets/notebook_detail.png" width="200px"/><br/><b>Notebook Detail</b></td>
  </tr>
  <tr>
    <td align="center"><img src="./assets/ai_chat.png" width="200px"/><br/><b>AI Chat</b></td>
    <td align="center"><img src="./assets/summary.png" width="200px"/><br/><b>Summary</b></td>
    <td align="center"><img src="./assets/personal.png" width="200px"/><br/><b>Profile</b></td>
  </tr>
</table>

<p align="center"><i>And more features like Settings, Notifications...</i></p>

---

## Student information

<p align="center">
  <a href="https://huit.edu.vn/">
    <img src="./assets/Logo%20HUIT-03.png" alt="HUIT Logo" width="450">
  </a>
</p>

| Student ID | Full name | GitHub | Email |
|:----------:|------------------|-----------------------------------------|------------------------|
| 2001230791 | Doan Tan Minh Tan | [TanDoan1234](https://github.com/TanDoan1234) | doanminhtan.dev@gmail.com |

---

## Purpose

**DocuMind** is an AI-powered personal notebook assistant designed to help students and researchers manage and summarize their documents efficiently. By leveraging advanced **Deep Learning** techniques, DocuMind allows users to upload documents (PDF, Docx) and receive high-quality summaries and context-aware insights, ensuring accurate information processing.

---

## 🧠 AI & Deep Learning Stack

The project applies state-of-the-art Deep Learning techniques to optimize Vietnamese document processing:

- **Document Processing:** Uses [IBM Docling](https://github.com/DS4SD/docling) for advanced layout analysis and high-quality Markdown extraction from complex documents (PDF, Docx, Pptx).
- **Large Language Models (LLM):** 
  - **Summarization:** Evaluated using both [BARTpho](https://huggingface.co/vinai/bartpho-word) and [ViT5](https://huggingface.co/VietAI/vit5-base) for optimal performance.
  - **Question Answering:** Comparative implementation of [PhoBERT](https://huggingface.co/vinai/phobert-base) and [XLM-RoBERTa](https://huggingface.co/facebook/xlm-roberta-base) for context-aware extraction.

---

## 📂 Directory layout

```text
DocuMind/
├── mobile/                      ← Flutter mobile application
├── backend/                     
│   ├── processor/               ← AI Pipeline (Docling, Embedding, Summarizer)
│   └── main.py                  ← FastAPI entry point
├── tests/                       ← Backend & AI testing scripts
├── ai/                          ← Pre-trained models and training results
├── assets/                      ← Project assets (logos, demo screenshots)
├── pyproject.toml               ← Dependency management (uv)
└── README.md                    ← Project overview (English)
```

---

## 🛠️ Development Setup

The project uses **`uv`** for extremely fast and consistent Python environment management.

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Flutter SDK (for mobile)

### Backend Setup & Testing
1. Install dependencies and sync the environment:
   ```bash
   uv sync
   ```
2. Run AI validation tests (Models will be downloaded on first run):
   - **Document Processing:** `uv run python tests/test_docling_processor.py`
   - **Semantic Similarity:** `uv run python tests/test_embedding_service.py`
   - **Summarization:** `uv run python tests/test_summarization.py`
   - **AI Question Answering:** `uv run python tests/test_qa.py`

3. Start the main server:
   ```bash
   uv run python backend/main.py
   ```

### Mobile Setup
1. Run the application:
   ```bash
   cd mobile
   flutter run
   ```

---

## 📚 Documentation

### Getting Started
- 📖 **[Introduction](./docs/en/INSTALLATION.md#introduction)** - Learn what DocuMind offers.
- ⚡ **[Quick Start](./docs/en/INSTALLATION.md#quick-start)** - Get up and running in 5 minutes.
- 🔧 **[Installation](./docs/en/INSTALLATION.md#installation)** - Comprehensive setup guide.

### User Guide
- 📱 **[Interface Overview](./docs/en/FEATURES.md#interface-overview)** - Understanding the layout.
- 📚 **[Notebooks](./docs/en/FEATURES.md#notebooks)** - Organizing your research.
- ✍️ **[Summarization](./docs/en/FEATURES.md#summarization)** - Document summary features.
- 💬 **[AI Chat](./docs/en/FEATURES.md#chat)** - AI conversations with your files.

### Advanced Topics
- ⚙️ **[Document Processor](./docs/en/DOCUMENT_PROCESSOR.md)** - Technical deep-dive into document processing.
- 🤖 **[AI Models](./docs/en/AI_MODELS.md)** - AI model configuration and details.
- 📂 **[AI Directory](./docs/en/AI_DIRECTORY.md)** - Understanding the AI research folder.
- 🚀 **[Deployment](./docs/en/DOCUMENT_PROCESSOR.md#deployment)** - Production deployment guides.

---