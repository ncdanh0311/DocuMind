#!/usr/bin/env python3
"""
Preprocess datasets for VietSumBot training
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from datasets import load_from_disk, Dataset
from transformers import AutoTokenizer
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_vietnews_for_vit5(dataset_path: str, tokenizer_name: str = "VietAI/vit5-base"):
    """Preprocess Vietnews for ViT5 summarization"""
    logger.info("Preprocessing Vietnews for ViT5...")

    try:
        # Load dataset
        dataset = load_from_disk(dataset_path)
        logger.info(f"Loaded dataset with splits: {list(dataset.keys())}")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

        def preprocess_function(examples):
            """Tokenize and prepare inputs for ViT5"""
            inputs = []
            targets = []

            for article, summary in zip(examples["article"], examples["summary"]):
                # Add prefix for controllable summarization
                # We'll add prefix during training, not here
                input_text = f"vietnews: {article}"
                target_text = summary

                inputs.append(input_text)
                targets.append(target_text)

            # Tokenize inputs
            model_inputs = tokenizer(
                inputs,
                max_length=1024,
                truncation=True,
                padding=False
            )

            # Tokenize targets
            with tokenizer.as_target_tokenizer():
                labels = tokenizer(
                    targets,
                    max_length=256,
                    truncation=True,
                    padding=False
                )

            model_inputs["labels"] = labels["input_ids"]
            return model_inputs

        # Apply preprocessing
        processed_dataset = dataset.map(
            preprocess_function,
            batched=True,
            batch_size=1000,
            remove_columns=dataset["train"].column_names
        )

        # Save processed dataset
        output_path = Path(dataset_path).parent / "vietnews_vit5"
        output_path.mkdir(exist_ok=True)
        processed_dataset.save_to_disk(str(output_path))

        logger.info(f"Saved processed Vietnews to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to preprocess Vietnews: {e}")
        return False

def preprocess_viquad_for_phobert(dataset_path: str, tokenizer_name: str = "vinai/phobert-base"):
    """Preprocess UIT-ViQuAD for PhoBERT QA"""
    logger.info("Preprocessing UIT-ViQuAD for PhoBERT...")

    try:
        # Load dataset
        dataset = load_from_disk(dataset_path)
        logger.info(f"Loaded dataset with splits: {list(dataset.keys())}")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

        def preprocess_function(examples):
            """Tokenize and prepare inputs for QA"""
            questions = examples["question"]
            contexts = examples["context"]
            answers = examples["answers"]

            inputs = tokenizer(
                questions,
                contexts,
                max_length=512,
                truncation="only_second",
                padding=False,
                return_offsets_mapping=True
            )

            # Process answers
            start_positions = []
            end_positions = []

            for i, answer_list in enumerate(answers):
                if len(answer_list["answer_start"]) == 0:
                    # No answer case
                    start_positions.append(0)
                    end_positions.append(0)
                else:
                    # Take first answer
                    start_char = answer_list["answer_start"][0]
                    end_char = start_char + len(answer_list["text"][0])

                    # Find token positions
                    offset_mapping = inputs["offset_mapping"][i]
                    start_token = None
                    end_token = None

                    for j, (offset_start, offset_end) in enumerate(offset_mapping):
                        if offset_start <= start_char < offset_end:
                            start_token = j
                        if offset_start < end_char <= offset_end:
                            end_token = j
                            break

                    if start_token is None or end_token is None:
                        start_token = 0
                        end_token = 0

                    start_positions.append(start_token)
                    end_positions.append(end_token)

            inputs["start_positions"] = start_positions
            inputs["end_positions"] = end_positions
            inputs.pop("offset_mapping")

            return inputs

        # Apply preprocessing
        processed_dataset = dataset.map(
            preprocess_function,
            batched=True,
            batch_size=1000,
            remove_columns=dataset["train"].column_names
        )

        # Save processed dataset
        output_path = Path(dataset_path).parent / "viquad_phobert"
        output_path.mkdir(exist_ok=True)
        processed_dataset.save_to_disk(str(output_path))

        logger.info(f"Saved processed UIT-ViQuAD to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to preprocess UIT-ViQuAD: {e}")
        return False

def preprocess_vlsp_ner(dataset_path: str, tokenizer_name: str = "vinai/phobert-base"):
    """Preprocess VLSP 2018 for PhoBERT NER"""
    logger.info("Preprocessing VLSP 2018 for PhoBERT NER...")

    try:
        # Check if dataset exists
        vlsp_path = Path(dataset_path)
        if not (vlsp_path / "train.txt").exists():
            logger.warning(f"VLSP dataset not found at {vlsp_path}. Please download manually first.")
            return False

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

        # BIEOS tag mapping
        tag_to_id = {
            "O": 0,
            "B-PER": 1, "I-PER": 2, "E-PER": 3, "S-PER": 4,
            "B-LOC": 5, "I-LOC": 6, "E-LOC": 7, "S-LOC": 8,
            "B-ORG": 9, "I-ORG": 10, "E-ORG": 11, "S-ORG": 12,
            "B-MISC": 13, "I-MISC": 14, "E-MISC": 15, "S-MISC": 16
        }

        def load_vlsp_file(file_path: str) -> List[Dict[str, Any]]:
            """Load VLSP NER file"""
            sentences = []
            current_sentence = {"tokens": [], "tags": []}

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        if current_sentence["tokens"]:
                            sentences.append(current_sentence)
                            current_sentence = {"tokens": [], "tags": []}
                    else:
                        parts = line.split("\t")
                        if len(parts) == 2:
                            token, tag = parts
                            current_sentence["tokens"].append(token)
                            current_sentence["tags"].append(tag)

            if current_sentence["tokens"]:
                sentences.append(current_sentence)

            return sentences

        def preprocess_function(sentences: List[Dict[str, Any]]):
            """Tokenize and align labels"""
            all_input_ids = []
            all_attention_masks = []
            all_labels = []

            for sentence in sentences:
                tokens = sentence["tokens"]
                tags = sentence["tags"]

                # Tokenize
                encoded = tokenizer(
                    tokens,
                    is_split_into_words=True,
                    max_length=256,
                    truncation=True,
                    padding=False
                )

                # Align labels
                word_ids = encoded.word_ids()
                aligned_labels = []

                for word_id in word_ids:
                    if word_id is None:
                        aligned_labels.append(-100)  # Special tokens
                    else:
                        tag = tags[word_id]
                        aligned_labels.append(tag_to_id.get(tag, 0))

                all_input_ids.append(encoded["input_ids"])
                all_attention_masks.append(encoded["attention_mask"])
                all_labels.append(aligned_labels)

            return {
                "input_ids": all_input_ids,
                "attention_mask": all_attention_masks,
                "labels": all_labels
            }

        # Load and preprocess each split
        splits = {}
        for split in ["train", "dev", "test"]:
            file_path = vlsp_path / f"{split}.txt"
            if file_path.exists():
                sentences = load_vlsp_file(str(file_path))
                processed = preprocess_function(sentences)
                splits[split] = Dataset.from_dict(processed)
                logger.info(f"Processed {split}: {len(sentences)} sentences")
            else:
                logger.warning(f"File {file_path} not found")

        # Create DatasetDict
        from datasets import DatasetDict
        processed_dataset = DatasetDict(splits)

        # Save processed dataset
        output_path = vlsp_path.parent / "vlsp_phobert"
        output_path.mkdir(exist_ok=True)
        processed_dataset.save_to_disk(str(output_path))

        # Save tag mapping
        with open(output_path / "tag_to_id.json", "w") as f:
            json.dump(tag_to_id, f, indent=2)

        logger.info(f"Saved processed VLSP to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to preprocess VLSP: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Preprocess datasets for VietSumBot")
    parser.add_argument("--input-dir", default="datasets/processed", help="Input directory")
    parser.add_argument("--vietnews", action="store_true", help="Preprocess Vietnews")
    parser.add_argument("--viquad", action="store_true", help="Preprocess UIT-ViQuAD")
    parser.add_argument("--vlsp", action="store_true", help="Preprocess VLSP")
    parser.add_argument("--all", action="store_true", help="Preprocess all datasets")

    args = parser.parse_args()

    if args.all:
        args.vietnews = True
        args.viquad = True
        args.vlsp = True

    if not any([args.vietnews, args.viquad, args.vlsp]):
        logger.info("Use --vietnews, --viquad, --vlsp, or --all to specify what to preprocess")
        return

    success = True

    if args.vietnews:
        vietnews_path = Path(args.input_dir) / "vietnews"
        if vietnews_path.exists():
            success &= preprocess_vietnews_for_vit5(str(vietnews_path))
        else:
            logger.warning(f"Vietnews dataset not found at {vietnews_path}")

    if args.viquad:
        viquad_path = Path(args.input_dir) / "viquad"
        if viquad_path.exists():
            success &= preprocess_viquad_for_phobert(str(viquad_path))
        else:
            logger.warning(f"UIT-ViQuAD dataset not found at {viquad_path}")

    if args.vlsp:
        vlsp_path = Path(args.input_dir) / "vlsp2018"
        success &= preprocess_vlsp_ner(str(vlsp_path))

    if success:
        logger.info("All preprocessing completed successfully!")
    else:
        logger.warning("Some preprocessing failed. Check logs above.")

if __name__ == "__main__":
    main()