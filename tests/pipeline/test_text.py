import hashlib
import json
from types import SimpleNamespace
import pytest
from ai.runtime.registry import Manifest, ModelRegistry, manifest_version
from ai.runtime.text import segmented_alignment, split_to_budget
from ai.src.metrics.metric_qa import QAMetrics, text_scores
from ai.benchmark import choose_threshold, rouge_scores, validate_dataset
from backend.processor.canonical import canonical_from_items, validate_spans


def test_unicode_source_offsets_global_order_and_real_pdf_pages():
    document = canonical_from_items([
        {"text": "Tiếng Việt 🐈", "provenance": [{"page_no": 2}, {"page_no": 3}]},
        {"text": "Mục hai", "section_path": "Chương 2", "provenance": [{"page_no": 4}]},
    ], paginated=True)
    chunks = document.chunks(lambda text: split_to_budget(text, len, 7, 2))
    assert [c["global_index"] for c in chunks] == list(range(len(chunks)))
    for chunk in chunks:
        assert document.text[chunk["start_offset"]:chunk["end_offset"]] == chunk["content"]
    assert chunks[0]["page_number"] == 2 and chunks[0]["page_end"] == 3
    assert chunks[-1]["section_path"] == "Chương 2"
    txt = canonical_from_items([{"text": "Không có trang", "provenance": [{"page_no": 7}]}], paginated=False)
    assert txt.sections[0]["page_start"] is None


def test_scan_requires_ocr_instead_of_empty_ready_document():
    with pytest.raises(ValueError, match="ERR_DOCUMENT_NEEDS_OCR"): canonical_from_items([], True)


@pytest.mark.parametrize("text", ["a" * 1001, "Tiếng Việt 🐈\n" * 100, "a b c d e f g h i"])
def test_token_budget_covers_every_character(text):
    spans = split_to_budget(text, len, 20, 4)
    validate_spans(text, spans)
    assert all(len(text[s["start"]:s["end"]]) <= 20 for s in spans)
    assert spans[0]["start"] == 0 and spans[-1]["end"] == len(text)


def test_bad_token_spans_are_rejected():
    with pytest.raises(ValueError): validate_spans("abcdef", [{"start": 0, "end": 2}, {"start": 3, "end": 6}])


def test_word_segmentation_preserves_raw_answer_span():
    raw = "Thành phố Hồ Chí Minh, Việt Nam."
    segmented = "Thành_phố Hồ_Chí_Minh , Việt_Nam ."
    mapping = segmented_alignment(raw, segmented)
    left, right = segmented.index("Hồ"), segmented.index(" ,")
    assert raw[mapping[left][0]:mapping[right - 1][1]] == "Hồ Chí Minh"
    with pytest.raises(ValueError, match="ALIGNMENT"): segmented_alignment(raw, "Hà Nội")


def test_registry_rejects_changed_weights_and_untracked_files(tmp_path):
    directory = tmp_path / "vit5"; (directory / "model").mkdir(parents=True)
    weights = directory / "model/weights.bin"; weights.write_bytes(b"trained-weights-fixture")
    payload = Manifest(id="vit5", task="summarization", version="pending", max_input_tokens=512,
        files={"model/weights.bin": hashlib.sha256(weights.read_bytes()).hexdigest()}).model_dump()
    payload["version"] = manifest_version(payload)
    (directory / "manifest.json").write_text(json.dumps(payload))
    registry = ModelRegistry(tmp_path)
    assert registry.bundle("vit5")[0].version == payload["version"]
    weights.write_bytes(b"changed-weights")
    with pytest.raises(FileNotFoundError, match="CHECKSUM"): registry.bundle("vit5")
    (directory / "model/extra.json").write_text("{}")
    with pytest.raises(FileNotFoundError, match="UNTRACKED"): registry.bundle("vit5")


def test_missing_capabilities_do_not_download_or_load_models(tmp_path):
    models = ModelRegistry(tmp_path).capabilities()["models"]
    assert len(models) == 6 and not any(m["ready"] for m in models)
    assert not list(tmp_path.iterdir())


def test_qa_metric_aggregates_windows_and_multiple_answers():
    features = [{"example_id": "a", "offset_mapping": [None, (0, 3)]},
                {"example_id": "a", "offset_mapping": [None, (4, 8)]}]
    examples = [{"id": "a", "context": "Sai đúng", "answers": {"text": ["đúng", "Đúng!"]}}]
    score = QAMetrics.for_dataset(features, examples)(SimpleNamespace(predictions=([[0, 1], [0, 9]], [[0, 1], [0, 9]])))
    assert score == {"exact_match": 100, "f1": 100}
    assert text_scores("", [""]) == (1, 1)


def test_calibration_abstains_on_high_scoring_negative():
    records = [{"score": 5, "answer": "đúng", "answers": ["đúng"]},
               {"score": 3, "answer": "sai", "answers": []}]
    assert choose_threshold(records, max_false_positive=0) == 5
    assert rouge_scores("Việt Nam", "Việt Nam") == {"rouge1": 1, "rouge2": 1, "rougeL": 1}


def test_benchmark_rejects_incomplete_or_fabricated_empty_corpus():
    with pytest.raises(ValueError, match="24"): validate_dataset({"documents": [], "questions": []})
