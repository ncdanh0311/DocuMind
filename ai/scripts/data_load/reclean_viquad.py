import os
import re
from datasets import load_from_disk

def clean_common_noise(text):
    if not text: return ""
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\s\d.,!?\-:;()_]', '', text)
    return text

def fix_answer_start(item):
    """Verify và fix answer_start sau khi clean context."""
    context = clean_common_noise(item['context'])
    question = clean_common_noise(item['question'])
    answers = item['answers']

    if answers and len(answers['text']) > 0:
        fixed_texts = []
        fixed_starts = []
        for text, start in zip(answers['text'], answers['answer_start']):
            # Tìm lại vị trí đúng trong context đã clean
            pos = context.find(text)
            if pos != -1:
                fixed_texts.append(text)
                fixed_starts.append(pos)
            # Nếu không tìm được thì bỏ qua example này
        answers = {'text': fixed_texts, 'answer_start': fixed_starts}

    return {
        'id': item['id'],
        'uit_id': item.get('uit_id', ''),
        'title': item.get('title', ''),
        'context': context,
        'question': question,
        'answers': answers,
        'is_impossible': item.get('is_impossible', False),
        'plausible_answers': item.get('plausible_answers', None),
    }

def main():
    qa_path = "datasets/processed/viquad"
    if not os.path.exists(qa_path):
        print(f"Khong tim thay: {qa_path}")
        return

    print("Dang re-clean ViQuAD (khong dung ViTokenizer)...")
    ds = load_from_disk(qa_path)
    ds_cleaned = ds.map(fix_answer_start, num_proc=4)

    # Verify
    wrong = 0
    for ex in ds_cleaned['train']:
        ans = ex['answers']
        if not ans or len(ans['text']) == 0:
            continue
        text = ans['text'][0]
        start = ans['answer_start'][0]
        extracted = ex['context'][start:start+len(text)]
        if extracted != text:
            wrong += 1
    print(f"Wrong answer_start sau fix: {wrong}/{len(ds_cleaned['train'])}")

    ds_cleaned.save_to_disk("datasets/cleaned/viquad")
    print("Luu xong: datasets/cleaned/viquad")

if __name__ == "__main__":
    main()
