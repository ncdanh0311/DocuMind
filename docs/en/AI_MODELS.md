# 🧠 AI Models Guide - DocuMind

<div align="right">
  🌍 <b><a href="../vi/AI_MODELS.md">Vietnamese Version</a></b>
</div>

DocuMind leverages a sophisticated suite of state-of-the-art Deep Learning models specifically optimized for the Vietnamese language. This guide provides technical details on the models used for summarization, question answering, and document processing.

---

## 📋 Model Overview

The project evaluates and implements two primary tasks using four different model architectures to compare performance and accuracy.

| Task | Models Used | Architecture |
|:---:|---|---|
| **Summarization** | BARTpho, ViT5 | Encoder-Decoder (Seq2Seq) |
| **Question Answering** | PhoBERT, XLM-RoBERTa | Encoder-only |
| **Document Processing** | Docling (IBM) | Hybrid Layout Analysis |

---

## 📝 1. Summarization Models

We utilize two state-of-the-art Sequence-to-Sequence models to generate concise summaries of long documents.

### **BARTpho** (`bartpho_summarization`)
- **Base Model:** `vinai/bartpho-word`
- **Description:** The first pre-trained sequence-to-sequence model for Vietnamese. It is particularly strong at capturing long-range dependencies and generating natural-sounding Vietnamese sentences.
- **Usage:** Generates high-quality, abstractive summaries.

### **ViT5** (`vit5_summarization`)
- **Base Model:** `VietAI/vit5-base`
- **Description:** A T5-based model pre-trained on a massive Vietnamese corpus. It follows the "Text-to-Text Transfer Transformer" paradigm.
- **Usage:** Excellent at understanding complex document structures and distilling key information.

---

## ❓ 2. Question Answering (QA) Models

These models are used to extract answers from document content based on user queries.

### **PhoBERT** (`phobert_qa`)
- **Base Model:** `vinai/phobert-base`
- **Description:** A state-of-the-art language model for Vietnamese based on the RoBERTa architecture. It excels at understanding the nuances of Vietnamese grammar and vocabulary.
- **Usage:** Used for precise fact extraction and context understanding.

### **XLM-RoBERTa** (`xlmroberta_qa`)
- **Base Model:** `xlm-roberta-base`
- **Description:** A multilingual model trained on 100 languages, including Vietnamese. 
- **Usage:** Provides a strong baseline for cross-lingual understanding and robust performance across different document styles.

---

## 🔍 3. Supportive Pipelines

### **Docling (by IBM)**
- **Role:** Document Ingestion.
- **Function:** Unlike traditional PDF parsers, Docling performs layout analysis to identify headers, tables, and images, converting them into clean Markdown. This prevents the AI from getting confused by page headers/footers or complex table structures.


---

## 🚀 How to use in Backend

The backend is designed to be model-agnostic. You can switch between these models in the configuration to compare results.

```python
# Example of switching summarization models
processor = Summarizer(model_path="ai/results/models/vit5_summarization")
# or
processor = Summarizer(model_path="ai/results/models/bartpho_summarization")
```

---

## 📊 Evaluation Results
*Detailed benchmark results (ROUGE scores for summarization, F1/EM for QA) can be found in the `ai/results/logs` directory.*
