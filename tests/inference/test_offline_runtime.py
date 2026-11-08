"""Tiny random local fixtures exercise serving only; these are NOT quality benchmarks."""
import json
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.processors import TemplateProcessing
from transformers import PreTrainedTokenizerFast, RobertaConfig, RobertaForQuestionAnswering, RobertaModel
from ai.import_model import import_bundle
from ai.runtime.models import ModelRuntime
from ai.runtime.registry import ModelRegistry, manifest_version


def source_checkpoint(path, with_head=True):
    vocab = {word: index for index, word in enumerate(['<s>', '<pad>', '</s>', '<unk>', 'Hà', 'Nội', 'ở', 'đâu', '?', 'Việt', 'Nam', '.'])}
    raw = Tokenizer(WordLevel(vocab, unk_token='<unk>')); raw.pre_tokenizer = Whitespace()
    raw.post_processor = TemplateProcessing(single='<s> $A </s>', pair='<s> $A </s> </s> $B:1 </s>:1',
        special_tokens=[('<s>', 0), ('</s>', 2)])
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=raw, bos_token='<s>', eos_token='</s>', cls_token='<s>', sep_token='</s>', pad_token='<pad>', unk_token='<unk>', model_max_length=62)
    config = RobertaConfig(vocab_size=len(vocab), hidden_size=16, num_hidden_layers=1, num_attention_heads=2,
        intermediate_size=32, max_position_embeddings=64, pad_token_id=1, type_vocab_size=2)
    model = RobertaForQuestionAnswering(config) if with_head else RobertaModel(config)
    model.save_pretrained(path); tokenizer.save_pretrained(path)
    return path


def test_import_forward_sliding_windows_and_abstention_are_offline(tmp_path, monkeypatch):
    from ai.services import qa_service as qa_module
    import importlib
    qa_module = importlib.import_module('ai.services.qa_service')
    source = source_checkpoint(tmp_path / 'source')
    root = tmp_path / 'bundles'
    imported = import_bundle('xlmroberta_qa', source, root / 'xlmroberta_qa', qa_threshold=-1e9)
    runtime = ModelRuntime(ModelRegistry(root)); monkeypatch.setattr(qa_module, 'runtime', runtime)
    raw = 'Hà Nội ở Việt Nam. ' * 100
    answer = qa_module.qa_service.answer([{'chunk_id': 'fixture', 'content': raw}], 'Hà Nội ở đâu?', 'xlmroberta_qa')
    assert answer['status'] == 'answered'
    assert raw[answer['start']:answer['end']] == answer['answer']
    assert answer['model_version'] == imported['version']
    manifest = root / 'xlmroberta_qa/manifest.json'
    payload = json.loads(manifest.read_text()); payload['qa_threshold'] = 1e9; payload['version'] = manifest_version(payload)
    manifest.write_text(json.dumps(payload))
    rejected = qa_module.qa_service.answer([{'chunk_id': 'fixture', 'content': raw}], 'ở đâu?', 'xlmroberta_qa')
    assert rejected['status'] == 'no_answer' and rejected['answer'] == '' and rejected['chunk_id'] is None


def test_base_model_does_not_silently_gain_random_qa_head(tmp_path):
    source = source_checkpoint(tmp_path / 'base', with_head=False)
    destination = tmp_path / 'bundles/xlmroberta_qa'
    with pytest.raises(ValueError, match='UNTRAINED_MODEL_HEAD'):
        import_bundle('xlmroberta_qa', source, destination)
    assert not destination.exists()


def test_training_processor_maps_overflow_windows_to_raw_phobert_answers(tmp_path):
    pytest.importorskip('pyvi')
    from ai.src.data.process_qa import QAProcessor
    from ai.runtime.text import segmented_alignment
    from pyvi import ViTokenizer
    raw = 'Thành phố Hồ Chí Minh, Việt Nam. '
    segmented_alignment(raw, ViTokenizer.tokenize(raw))
    source = source_checkpoint(tmp_path / 'source')
    tokenizer = PreTrainedTokenizerFast.from_pretrained(source)
    context = 'Việt Nam. ' * 80 + 'Hà Nội ở Việt Nam.'
    start = context.index('Hà Nội')
    processor = QAProcessor(tokenizer, max_length=384, word_segment=True)
    features = processor.process({'id': ['source'], 'question': ['ở đâu?'], 'context': [context],
        'answers': [{'text': ['Hà Nội'], 'answer_start': [start]}]})
    assert len(features['input_ids']) > 1
    assert all(len(ids) <= 62 for ids in features['input_ids'])
    answered = [i for i, label in enumerate(features['start_positions']) if label > 0]
    assert answered
    for i in answered:
        left = features['offset_mapping'][i][features['start_positions'][i]][0]
        right = features['offset_mapping'][i][features['end_positions'][i]][1]
        assert context[left:right] == 'Hà Nội'


def test_docx_provenance_has_global_order_without_fabricated_pages(tmp_path):
    pytest.importorskip('docling')
    from docx import Document
    from backend.processor.document_processor import DocumentProcessor
    document = Document(); document.add_heading('Chương đầu', 1); document.add_paragraph('Đoạn đầu tiên.')
    document.add_heading('Chương cuối', 1); document.add_paragraph('Kết luận cuối cùng.')
    path = tmp_path / 'source.docx'; document.save(path)
    canonical = DocumentProcessor().extract(str(path))
    assert 'Kết luận cuối cùng.' in canonical.text
    chunks = canonical.chunks(lambda text: [{'start': 0, 'end': len(text)}])
    assert all(c['page_number'] is None and c['page_end'] is None for c in chunks)
    assert chunks[-1]['section_path'] == 'Chương cuối'
