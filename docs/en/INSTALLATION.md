# 🚀 Getting Started - DocuMind

<div align="right">
  🌍 <b><a href="../vi/INSTALLATION.md">Vietnamese Version</a></b>
</div>

## <a name="introduction"></a>📖 Introduction

**DocuMind** is an AI-powered assistant designed to help researchers and students handle Vietnamese documents with ease. By combining Docling's advanced extraction with state-of-the-art LLMs, we provide a unified platform for summarization and document interaction.

---

## <a name="quick-start"></a>⚡ Quick Start

To get DocuMind running in less than 5 minutes:
1. Ensure `uv` and `Flutter` are installed.
2. Run `uv sync` in the root directory.
3. Run `uv run python tests/test_docling_processor.py` to warm up the models.
4. Run `uv run python backend/main.py`.

---

## <a name="installation"></a>🔧 Installation

### Backend Setup
1. **Python Environment:** Use `uv` for consistent dependency management.
   ```bash
   uv sync
   ```
2. **AI Models:** Models are loaded dynamically from the `ai/results/models` directory.

### Mobile Setup
1. **Navigate to mobile:** `cd mobile`
2. **Install deps:** `flutter pub get`
3. **Run:** `flutter run`
