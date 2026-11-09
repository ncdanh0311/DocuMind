from ai.runtime.text import segmented_alignment

class QAProcessor:
    def __init__(self, tokenizer, max_length=384, doc_stride=96, word_segment=None):
        if not tokenizer.is_fast: raise ValueError("QA requires a fast tokenizer")
        self.tokenizer = tokenizer
        self.max_length = min(max_length, tokenizer.model_max_length)
        self.doc_stride = min(doc_stride, self.max_length // 4)
        self.word_segment = "phobert" in tokenizer.name_or_path.lower() if word_segment is None else word_segment

    def process(self, examples):
        questions, contexts, mappings = [], [], []
        for question, raw in zip(examples["question"], examples["context"]):
            if self.word_segment:
                from pyvi import ViTokenizer
                context, question = ViTokenizer.tokenize(raw), ViTokenizer.tokenize(question)
                mapping = segmented_alignment(raw, context)
            else: context, mapping = raw, [(i, i + 1) for i in range(len(raw))]
            questions.append(question); contexts.append(context); mappings.append(mapping)
        encoded = self.tokenizer(questions, contexts, truncation="only_second", max_length=self.max_length,
            stride=self.doc_stride, return_overflowing_tokens=True, return_offsets_mapping=True, padding="max_length")
        samples = encoded.pop("overflow_to_sample_mapping")
        offsets = encoded["offset_mapping"]
        starts, ends, ids, raw_offsets = [], [], [], []
        for feature, sample in enumerate(samples):
            sequence_ids = encoded.sequence_ids(feature)
            mapping = mappings[sample]
            feature_offsets = []
            for index, (left, right) in enumerate(offsets[feature]):
                feature_offsets.append((mapping[left][0], mapping[right - 1][1]) if sequence_ids[index] == 1 and right > left else None)
            raw_offsets.append(feature_offsets)
            ids.append(str(examples["id"][sample]))
            answers = examples["answers"][sample]
            start_label = end_label = 0
            for gold, left in zip(answers["text"], answers["answer_start"]):
                right = left + len(gold)
                if examples["context"][sample][left:right] != gold: raise ValueError("ERR_INVALID_GOLD_OFFSET")
                valid = [(i, span) for i, span in enumerate(feature_offsets) if span is not None]
                if valid and valid[0][1][0] <= left and valid[-1][1][1] >= right:
                    first = next((i for i, span in valid if span[0] <= left < span[1]), None)
                    last = next((i for i, span in reversed(valid) if span[0] < right <= span[1]), None)
                    if first is None or last is None: raise ValueError("ERR_GOLD_TOKEN_ALIGNMENT")
                    start_label, end_label = first, last
                    break
            starts.append(start_label); ends.append(end_label)
        encoded["offset_mapping"], encoded["example_id"] = raw_offsets, ids
        encoded["start_positions"], encoded["end_positions"] = starts, ends
        return encoded
