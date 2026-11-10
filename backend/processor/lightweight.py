"""Bounded text-only parser subprocess. Never imports inference or OCR libraries."""
import json
from pathlib import Path
import sys
import zipfile
from backend.processor.canonical import canonical_from_items


def extract(path: Path, max_pages: int, max_characters: int):
    items, length = [], 0
    def append(text, section="Nội dung", page=None):
        nonlocal length
        if not text.strip(): return
        length += len(text) + (2 if items else 0)
        if length > max_characters: raise ValueError("ERR_TEXT_TOO_LARGE")
        items.append({"text": text, "section_path": section,
                      "provenance": [{"page_no": page}] if page else []})
    suffix = path.suffix.lower()
    if suffix == ".txt":
        try: append(path.read_text(encoding="utf-8-sig"))
        except UnicodeDecodeError: raise ValueError("ERR_TEXT_ENCODING") from None
    elif suffix == ".pdf":
        import pymupdf
        with pymupdf.open(path) as document:
            if document.needs_pass: raise ValueError("ERR_DOCUMENT_PASSWORD")
            if len(document) > max_pages: raise ValueError("ERR_TOO_MANY_PAGES")
            for index, page in enumerate(document): append(page.get_text(sort=True), f"Trang {index + 1}", index + 1)
    elif suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > 5000 or sum(entry.file_size for entry in entries) > 50 * 1024 * 1024:
                raise ValueError("ERR_DOCUMENT_TOO_COMPLEX")
            if "word/document.xml" not in archive.namelist(): raise ValueError("ERR_FILE_FORMAT")
        from docx import Document
        from docx.text.paragraph import Paragraph
        section = "Nội dung"
        for block in Document(path).iter_inner_content():
            if isinstance(block, Paragraph):
                if block.style and block.style.name.startswith("Heading"): section = block.text or section
                append(block.text, section)
            else:
                for row in block.rows: append("\t".join(cell.text for cell in row.cells), section)
    else: raise ValueError("ERR_FILE_FORMAT")
    result = canonical_from_items(items, suffix == ".pdf")
    if len(result.text) > max_characters: raise ValueError("ERR_TEXT_TOO_LARGE")
    return {"text": result.text, "sections": result.sections}


def main():
    path, output, pages, characters = sys.argv[1:]
    try:
        import resource
        _, hard = resource.getrlimit(resource.RLIMIT_AS)
        budget = 256 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (budget if hard < 0 else min(budget, hard), hard))
    except (ImportError, OSError, ValueError): pass
    try: result = extract(Path(path), int(pages), int(characters))
    except MemoryError: result = {"error": "ERR_DOCUMENT_TOO_COMPLEX"}
    except ValueError as exc:
        code = str(exc)
        result = {"error": code if code.startswith("ERR_") else "ERR_FILE_FORMAT"}
    except Exception: result = {"error": "ERR_FILE_FORMAT"}
    Path(output).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__": main()
