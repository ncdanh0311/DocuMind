"""Canonical text and verifiable source ranges, independent of inference libraries."""
from dataclasses import dataclass
import hashlib
import json

PIPELINE_VERSION = "canonical-v1"

@dataclass
class CanonicalDocument:
    text: str
    sections: list[dict]

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    def chunks(self, split) -> list[dict]:
        chunks = []
        for section in self.sections:
            text = self.text[section["start"]:section["end"]]
            if not text.strip(): continue
            spans = split(text)
            validate_spans(text, spans)
            for span in spans:
                start = section["start"] + span["start"]
                end = section["start"] + span["end"]
                chunks.append({"global_index": len(chunks), "content": self.text[start:end],
                    "start_offset": start, "end_offset": end, "page_number": section.get("page_start"),
                    "page_end": section.get("page_end"), "section_path": section.get("section_path"),
                    "provenance": section.get("provenance", [])})
        return chunks

def validate_spans(text: str, spans: list[dict]) -> None:
    covered = 0
    for span in spans:
        start, end = span["start"], span["end"]
        if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(text) or start > covered:
            raise ValueError("ERR_INVALID_TOKEN_SPANS")
        covered = max(covered, end)
    if text and covered != len(text): raise ValueError("ERR_INCOMPLETE_TOKEN_COVERAGE")

def canonical_from_items(items: list[dict], paginated: bool) -> CanonicalDocument:
    parts, sections, position = [], [], 0
    for item in items:
        # Preserve original characters: provenance and all answer offsets reference this exact string.
        text = item["text"]
        if not text.strip(): continue
        if parts:
            parts.append("\n\n")
            position += 2
        start = position
        parts.append(text)
        position += len(text)
        provenance = item.get("provenance", [])
        pages = [p["page_no"] for p in provenance if isinstance(p.get("page_no"), int) and p["page_no"] > 0] if paginated else []
        sections.append({"start": start, "end": position, "section_path": item.get("section_path", "Nội dung"),
                         "item_ref": item.get("item_ref"), "provenance": provenance,
                         "page_start": min(pages) if pages else None, "page_end": max(pages) if pages else None})
    if not parts: raise ValueError("ERR_DOCUMENT_NEEDS_OCR" if paginated else "ERR_EMPTY_DOCUMENT")
    return CanonicalDocument("".join(parts), sections)
