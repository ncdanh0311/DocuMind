import os
import logging
import uuid
from sqlmodel import Session
from backend.app.core.db import engine
from backend.app.models.models import Document, DocumentChunk, Notification
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

            # Sinh vector embedding hàng loạt (batch) cho tất cả các chunks
            from backend.app.services.embedding_service import embedding_service
            contents = [chunk["content"] for chunk in chunks_data]
            embeddings = embedding_service.embed_text(contents, is_query=False)

            for idx, chunk in enumerate(chunks_data):
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
                    embedding=embeddings[idx],
                    embedding_model="intfloat/multilingual-e5-small",
                    page_number=page_num
                )
                session.add(db_chunk)

            # Tạo thông báo thành công cho người dùng sở hữu tài liệu
            notification = Notification(
                user_id=doc.notebook.user_id,
                title="Phân tích tài liệu thành công!",
                body=f"Tài liệu {doc.file_name} đã được phân tích thành công! Bắt đầu tóm tắt ngay.",
                type="success"
            )
            session.add(notification)

            doc.status = "ready"
            session.commit()
            logger.info(f"Xử lý thành công tài liệu {doc_id}. Đã tạo {len(chunks_data)} chunks.")

        except Exception as e:
            logger.error(f"Lỗi xử lý tài liệu {doc_id}: {e}", exc_info=True)
            try:
                notification = Notification(
                    user_id=doc.notebook.user_id,
                    title="Lỗi phân tích tài liệu",
                    body=f"Tài liệu {doc.file_name} gặp lỗi khi phân tích: {str(e)}",
                    type="error"
                )
                session.add(notification)
            except Exception as notify_err:
                logger.error(f"Không thể tạo thông báo lỗi cho user: {notify_err}")
            
            doc.status = "error"
            session.commit()
