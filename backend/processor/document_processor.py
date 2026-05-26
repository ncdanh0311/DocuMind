from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from typing import List, Dict, Any, Optional
import os
import logging
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Service xử lý tài liệu: Trích xuất nội dung từ PDF/Docx bằng Docling
    và phân mảnh văn bản thông minh bằng cơ chế 2 lớp (Structural + Recursive).
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, do_ocr: bool = False):
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
        
        # 3. Cấu hình bộ cắt văn bản (Dùng chung cho các lần gọi)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " "]
        )

    def _inject_markdown_headers(self, md_content: str) -> str:
        """Nhận diện các mẫu đánh số thủ công và tiêm Header Markdown theo cấp bậc."""
        lines = md_content.split("\n")
        processed_lines = []
        for line in lines:
            stripped = line.strip()
            # Nếu đã là Header của Docling thì giữ nguyên
            if stripped.startswith("#"):
                processed_lines.append(line)
                continue

            # 1. Cấp 1: Số La Mã (I., II., VI...) - Thường là tiêu đề lớn
            if re.match(r'^(\*\*|)\s*([IVXLC]+\.)\s+[A-ZĐ]', stripped):
                clean_line = stripped.replace("**", "").strip()
                processed_lines.append(f"# {clean_line}")
            # 2. Cấp 2: Số Arab (1., 1.1...) - Thường là tiêu đề mục
            elif re.match(r'^(\*\*|)\s*(\d+\.\d+\.?)\s+', stripped):
                clean_line = stripped.replace("**", "").strip()
                processed_lines.append(f"## {clean_line}")
            else:
                processed_lines.append(line)
        return "\n".join(processed_lines)

    def extract_metadata(self, md_content: str) -> Dict[str, Any]:
        """Trích xuất thông tin Metadata của tài liệu."""
        preview = md_content[:1000]
        lines = [l.strip() for l in preview.split("\n") if l.strip()]
        
        # Tìm tiêu đề thực sự (dòng đầu tiên có chữ hoặc có Header)
        suggested_title = "Tài liệu không tên"
        for line in lines:
            clean = line.replace("#", "").replace("**", "").strip()
            if clean:
                suggested_title = clean
                break

        return {
            "title": suggested_title,
            "char_count": len(md_content),
            "word_count": len(md_content.split()),
            "estimated_reading_time": max(1, len(md_content.split()) // 200),
            "format": "Markdown (via Docling)"
        }

    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Quy trình xử lý toàn diện tài liệu.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        logger.info(f"🚀 Bắt đầu xử lý: {os.path.basename(file_path)}")
        
        # 1. Trích xuất text Markdown
        result = self.converter.convert(file_path)
        raw_md = result.document.export_to_markdown()
        
        # 1.1. Làm sạch HTML entities (như &amp;)
        import html
        raw_md = html.unescape(raw_md)
        
        # 2. Chuẩn hóa và gán Header thủ công
        md_content = self._inject_markdown_headers(raw_md)
        
        # 3. Phân tách lớp 1: Theo cấu trúc chương hồi
        sections = self.header_splitter.split_text(md_content)
        
        final_chunks = []
        # 4. Phân tách lớp 2: Recursive splitting cho các chương dài
        for i, section in enumerate(sections):
            # Xác định tên chương
            header_text = " > ".join([v for k, v in section.metadata.items()])
            if not header_text:
                header_text = "Nội dung chung"
            
            # Chia nhỏ chương nếu vượt quá chunk_size
            sub_chunks = self.text_splitter.split_text(section.page_content)
            
            for j, sub_content in enumerate(sub_chunks):
                final_chunks.append({
                    "id": f"s{i}_c{j}",
                    "header": header_text,
                    "content": sub_content,
                    "metadata": {
                        **section.metadata,
                        "chunk_index": j,
                        "is_sub_chunk": len(sub_chunks) > 1
                    }
                })
        
        return final_chunks

    @staticmethod
    def split_text_without_word_splitting(text: str, chunk_size: int = 1000, chunk_overlap: int = 0) -> List[str]:
        """
        Chia nhỏ văn bản một cách thông minh phục vụ cho việc tóm tắt và chat với AI (RAG),
        đảm bảo không bao giờ bị cắt ở giữa từ bằng cách loại bỏ separator rỗng.
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " "]
        )
        return splitter.split_text(text)
