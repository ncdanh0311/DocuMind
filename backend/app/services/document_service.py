import os
import logging
import uuid
from sqlmodel import Session
from backend.app.core.db import engine
from backend.app.models.models import Document, DocumentChunk
from backend.processor.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

def process_document_background(doc_id: uuid.UUID, file_path: str):
    """
    Tác vụ nền xử lý tài liệu bằng Docling và lưu các phân mảnh (chunks) vào Database.
    """
    logger.info(f"⚡ Bắt đầu xử lý nền tài liệu: {doc_id}")
    with Session(engine) as session:
        doc = session.get(Document, doc_id)
        if not doc:
            logger.error(f"Không tìm thấy Document {doc_id} trong DB")
            return

        doc.status = "processing"
        session.commit()

        try:
            processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
            chunks_data = processor.process_document(file_path)

            for chunk in chunks_data:
                page_num = 1
                if "metadata" in chunk and "page" in chunk["metadata"]:
                    try:
                        page_num = int(chunk["metadata"]["page"])
                    except (ValueError, TypeError):
                        pass

                db_chunk = DocumentChunk(
                    docuchunk_id=uuid.uuid4(),
                    document_id=doc_id,
                    content=chunk["content"],
                    page_number=page_num
                )
                session.add(db_chunk)

            doc.status = "ready"
            session.commit()
            logger.info(f"✅ Xử lý thành công tài liệu {doc_id}. Đã tạo {len(chunks_data)} chunks.")

        except Exception as e:
            logger.error(f"❌ Lỗi xử lý tài liệu {doc_id}: {e}", exc_info=True)
            doc.status = "error"
            session.commit()
