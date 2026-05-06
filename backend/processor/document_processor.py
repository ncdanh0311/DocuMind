from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100, do_ocr: bool = False):
        # 1. Cấu hình Pipeline cho PDF (Docling)
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = do_ocr
        
        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
        
        # 2. Khởi tạo bộ chuyển đổi của Docling
        self.converter = DocumentConverter(
            format_options=format_options
        )
        
        # 3. Khởi tạo bộ cắt văn bản (LangChain)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Quy trình xử lý:
        1. Docling: Tài liệu (PDF/Docx/...) -> Markdown
        2. TextSplitter: Markdown -> Chunks
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        logger.info(f"Đang xử lý tài liệu: {os.path.basename(file_path)}")

        # Bước 1: Trích xuất nội dung bằng Docling
        result = self.converter.convert(file_path)
        markdown_content = result.document.export_to_markdown()
        
        # Bước 2: Cắt nhỏ nội dung để chuẩn bị cho Summarization/QA
        chunks_text = self.text_splitter.split_text(markdown_content)
        
        processed_chunks = []
        for i, text in enumerate(chunks_text):
            processed_chunks.append({
                "content": text,
                "metadata": {
                    "source": os.path.basename(file_path),
                    "chunk_index": i,
                    "format": "markdown"
                }
            })
            
        logger.info(f"Đã xử lý xong {len(processed_chunks)} mảnh văn bản.")
        return processed_chunks

# Demo nhanh cách dùng
if __name__ == "__main__":
    processor = DocumentProcessor(do_ocr=False)
    print("DocumentProcessor initialized (No Embedding).")
