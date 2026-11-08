"""Token budgets and character alignment, without heavyweight imports."""
def split_to_budget(text: str, count_tokens, budget: int, overlap: int = 0) -> list[dict]:
    if not text: return []
    spans, start = [], 0
    while start < len(text):
        low, high = start + 1, len(text)
        end = start
        while low <= high:
            middle = (low + high) // 2
            if count_tokens(text[start:middle]) <= budget: end, low = middle, middle + 1
            else: high = middle - 1
        if end == start: raise ValueError("ERR_TOKEN_BUDGET")
        if end < len(text):
            boundary = text.rfind(" ", start + 1, end)
            if boundary > start: end = boundary + 1
        while end > start and count_tokens(text[start:end]) > budget: end -= 1
        if end <= start: raise ValueError("ERR_TOKEN_BUDGET")
        spans.append({"start": start, "end": end})
        if end == len(text): break
        next_start = end
        if overlap:
            # A bounded token suffix, never a fixed character approximation.
            for candidate in range(end - 1, start, -1):
                if count_tokens(text[candidate:end]) > overlap: break
                next_start = candidate
        start = max(start + 1, next_start)
    return spans

def segmented_alignment(raw: str, segmented: str) -> list[tuple[int, int]]:
    mapping, index = [], 0
    for char in segmented:
        if index < len(raw) and raw[index] == char:
            mapping.append((index, index + 1)); index += 1; continue
        if char.isspace() or char == "_":
            start = index
            while index < len(raw) and raw[index].isspace(): index += 1
            mapping.append((start, index)); continue
        while index < len(raw) and raw[index].isspace(): index += 1
        if index >= len(raw) or raw[index] != char: raise ValueError("ERR_TOKEN_ALIGNMENT")
        mapping.append((index, index + 1)); index += 1
    if raw[index:].strip(): raise ValueError("ERR_TOKEN_ALIGNMENT")
    return mapping
