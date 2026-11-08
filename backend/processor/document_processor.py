"""Docling ingestion preserving item provenance rather than flattening page information."""
from pathlib import Path
from backend.processor.canonical import CanonicalDocument, canonical_from_items

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, do_ocr: bool = False):
        self.do_ocr = do_ocr
        self.converter = None

    def extract(self, file_path: str) -> CanonicalDocument:
        path = Path(file_path)
        if not path.is_file(): raise FileNotFoundError("ERR_SOURCE_MISSING")
        if path.suffix.lower() == ".txt":
            return canonical_from_items([{"text": path.read_text(encoding="utf-8-sig"), "section_path": "Nội dung"}], False)
        if self.converter is None:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            self.converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=PdfPipelineOptions(do_ocr=self.do_ocr))})
        result = self.converter.convert(path)
        items, headings = [], []
        for item, depth in result.document.iterate_items():
            label = str(getattr(getattr(item, "label", None), "value", ""))
            if hasattr(item, "text"):
                text = item.text
            elif label == "table":
                text = item.export_to_markdown(result.document)
            else:
                continue
            if label in ("title", "section_header"):
                level = max(1, int(getattr(item, "level", 1)))
                headings = headings[:level - 1] + [text]
            provenance = [p.model_dump(mode="json") for p in getattr(item, "prov", [])]
            items.append({"text": text, "section_path": " > ".join(headings) or "Nội dung", "item_ref": item.self_ref, "provenance": provenance})
        return canonical_from_items(items, path.suffix.lower() == ".pdf")

    def process_document(self, file_path: str, split=None) -> list[dict]:
        if split is None:
            from backend.app.services.ai_client import ai_client
            split = lambda text: ai_client.split(text, "embedding", overlap=64)
        return self.extract(file_path).chunks(split)
