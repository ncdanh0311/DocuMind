from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import os

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        # Khởi tạo bộ chuyển đổi của Docling
        self.converter = DocumentConverter()
        
        # Khởi tạo bộ cắt văn bản (Dùng sau khi Docling xuất ra Markdown)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Quy trình xử lý bằng Docling:
        1. Chuyển đổi tài liệu (PDF/Docx/PPTX) sang cấu trúc Docling.
        2. Xuất bản sang định dạng Markdown (để giữ cấu trúc bảng, tiêu đề).
        3. Cắt nhỏ (Chunking) văn bản Markdown.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        # Bước 1: Convert tài liệu
        result = self.converter.convert(file_path)
        
        # Bước 2: Xuất ra Markdown
        markdown_content = result.document.export_to_markdown()
        
        # Bước 3: Cắt nhỏ nội dung Markdown
        # Markdown giúp AI hiểu rõ các phần tiêu đề và bảng hơn text thô
        chunks_text = self.text_splitter.split_text(markdown_content)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks_text):
            processed_chunks.append({
                "content": chunk,
                "metadata": {
                    "source": os.path.basename(file_path),
                    "chunk_index": i,
                    "format": "markdown"
                }
            })
            
        return processed_chunks

# Demo nhanh cách dùng
if __name__ == "__main__":
    # Ví dụ cách sử dụng (Cần cài đặt thư viện docling trước để chạy)
    processor = DocumentProcessor()
    print("Docling Processor initialized successfully.")
    print("Ready to process PDF, Docx, and more with high accuracy.")
