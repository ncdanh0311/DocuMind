import sys
import os
import uuid
from sqlmodel import Session, create_engine, select
from sqlalchemy import text

# Thêm thư mục root vào sys.path để import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.models.models import User, Notebook, Document, DocumentChunk
from backend.app.services.embedding_service import embedding_service

def test_db_embedding_integration():
    print("🚀 Khởi chạy test tích hợp Postgres + pgvector (384 chiều)...")
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with Session(engine) as session:
            # 1. Tìm hoặc tạo user và notebook test
            user = session.exec(select(User)).first()
            created_test_user = False
            if not user:
                print("👤 DB chưa có user, đang tạo user tạm thời...")
                user = User(
                    user_id=uuid.uuid4(),
                    email="test_embedding_user@example.com",
                    hashed_password="hashedpassword123",
                    full_name="User Kiểm Thử"
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                created_test_user = True
            
            notebook = session.exec(select(Notebook).where(Notebook.user_id == user.user_id)).first()
            created_test_notebook = False
            if not notebook:
                print("📓 DB chưa có notebook, đang tạo notebook tạm thời...")
                notebook = Notebook(
                    notebook_id=uuid.uuid4(),
                    user_id=user.user_id,
                    title="Sổ tay kiểm thử",
                    is_private=True
                )
                session.add(notebook)
                session.commit()
                session.refresh(notebook)
                created_test_notebook = True
                
            print(f"Sử dụng Notebook test: {notebook.title} (ID: {notebook.notebook_id})")
            
            # 2. Tạo tài liệu ảo
            doc_id = uuid.uuid4()
            test_doc = Document(
                document_id=doc_id,
                notebook_id=notebook.notebook_id,
                file_name="test_embedding_integration.txt",
                status="processing"
            )
            session.add(test_doc)
            session.commit()
            
            # 3. Tạo chunks và sinh vector embedding
            content_passage = "Học sâu (Deep Learning) là một phân ngành của trí tuệ nhân tạo."
            content_other = "Trái đất quay quanh mặt trời mất khoảng 365 ngày."
            
            print("⚙️ Sinh vector cho 2 chunks kiểm thử...")
            vectors = embedding_service.embed_text([content_passage, content_other], is_query=False)
            
            chunk_1 = DocumentChunk(
                docuchunk_id=uuid.uuid4(),
                document_id=doc_id,
                content=content_passage,
                embedding=vectors[0],
                embedding_model="intfloat/multilingual-e5-small",
                page_number=1
            )
            chunk_2 = DocumentChunk(
                docuchunk_id=uuid.uuid4(),
                document_id=doc_id,
                content=content_other,
                embedding=vectors[1],
                embedding_model="intfloat/multilingual-e5-small",
                page_number=1
            )
            
            session.add(chunk_1)
            session.add(chunk_2)
            session.commit()
            print("✅ Đã ghi thành công 2 chunks có chứa vector 384 chiều vào Database Postgres.")
            
            # 4. Thực hiện truy vấn ngữ nghĩa (Semantic Search) bằng pgvector khoảng cách cosine (<=>)
            query = "Trí tuệ nhân tạo và học sâu"
            print(f"🔍 Thực hiện câu hỏi truy vấn: '{query}'")
            query_vector = embedding_service.embed_text([query], is_query=True)[0]
            
            # Thực hiện sắp xếp theo khoảng cách cosine của pgvector (nhỏ nhất là tương đồng nhất)
            # Chúng ta dùng toán tử <=> của pgvector qua câu lệnh SQL thô hoặc ORM helper
            statement = (
                select(DocumentChunk)
                .where(DocumentChunk.document_id == doc_id)
                .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
                .limit(1)
            )
            
            best_match = session.exec(statement).first()
            
            print("\n" + "="*50)
            print("KẾT QUẢ SEMANTIC SEARCH:")
            print("="*50)
            if best_match:
                print(f"Đoạn tương đồng nhất tìm thấy: {best_match.content}")
                print(f"Khớp đúng đoạn cần tìm: {best_match.content == content_passage}")
                assert best_match.content == content_passage, "Lỗi: Hệ thống không trả về đoạn liên quan nhất."
            else:
                print("❌ Không tìm thấy đoạn nào.")
                
            print("="*50)
            
            # 5. Dọn dẹp dữ liệu test
            print("🧹 Đang dọn dẹp dữ liệu kiểm thử...")
            session.delete(test_doc) # Cascade sẽ tự xoá chunks
            if created_test_notebook:
                session.delete(notebook)
            if created_test_user:
                session.delete(user)
            session.commit()
            print("✨ Kiểm thử tích hợp Postgres + pgvector thành công tốt đẹp!")
            
    except Exception as e:
        print(f"❌ Lỗi trong quá trình kiểm thử tích hợp: {e}")
        raise e

if __name__ == "__main__":
    test_db_embedding_integration()
