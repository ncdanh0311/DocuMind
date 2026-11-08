class SumProcessor:
    def __init__(self, tokenizer, max_input_length=512, max_target_length=256, word_segment=False):
        self.tokenizer, self.max_input_length, self.max_target_length = tokenizer, max_input_length, max_target_length
        self.word_segment = word_segment

    def process(self, examples):
        articles = examples["article"]
        targets = examples.get("abstract", examples.get("summary"))
        if targets is None: raise ValueError("Summarization data requires abstract or summary")
        if self.word_segment:
            from pyvi import ViTokenizer
            articles = [ViTokenizer.tokenize(text) for text in articles]
            targets = [ViTokenizer.tokenize(text) for text in targets]
        encoded = self.tokenizer(["summarize: " + text for text in articles], max_length=self.max_input_length, truncation=True)
        encoded["labels"] = self.tokenizer(text_target=targets, max_length=self.max_target_length, truncation=True)["input_ids"]
        return encoded
