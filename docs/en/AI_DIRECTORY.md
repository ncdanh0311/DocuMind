# 📂 AI Directory Guide - DocuMind

<div align="right">
  🌍 <b><a href="../vi/AI_DIRECTORY.md">Vietnamese Version</a></b>
</div>

The `ai/` directory is the core research and development hub of DocuMind. It contains everything related to model training, evaluation, datasets, and experiment management.

---

## 🏗️ Directory Structure

| Directory/File | Description |
|---|---|
| **`src/`** | Core Python source code for model training, data preprocessing, and evaluation logic. |
| **`scripts/`** | Shell scripts (`.sh`) and utility scripts to automate training jobs and batch processing. |
| **`configs/`** | Configuration files (YAML/JSON) containing hyperparameters, model paths, and dataset settings. |
| **`datasets/`** | Training, validation, and testing datasets (CSV, JSON, or raw text). |
| **`results/`** | Final trained models, evaluation logs, and performance metrics. |
| **`checkpoints/`** | Intermediate model weights saved during training to allow resuming from failures. |
| **`hf_cache/`** | Local cache for HuggingFace models and tokenizers to avoid redundant downloads. |
| **`README.md`** | Specific instructions for the AI research component. |

---

## ⚙️ AI Workflow

The typical workflow within this directory follows these stages:

1.  **Data Preparation (`datasets/`):** Raw data is collected and preprocessed using scripts in `src/`.
2.  **Configuration (`configs/`):** Training parameters (learning rate, batch size, epochs) are defined.
3.  **Training (`src/` & `scripts/`):** Models (ViT5, BARTpho, etc.) are trained, with progress saved in `checkpoints/`.
4.  **Evaluation (`results/`):** The final models are evaluated on test sets, and logs are generated.
5.  **Deployment:** Successful models from `results/models/` are integrated into the `backend/` for production use.

---

## 📊 Experiments & Logs

All training logs and metrics (Loss, Accuracy, ROUGE scores, F1) are stored in `ai/results/logs/`. These logs are crucial for comparing the performance of different architectures (e.g., comparing BARTpho vs. ViT5 for summarization).

---
