import sys
import os
from sqlalchemy import text
from sqlmodel import Session, create_engine

# Thêm thư mục root vào sys.path để import các models và settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.models.models import SQLModel

def reset_entire_database():
    print(f"Kết nối tới cơ sở dữ liệu: {settings.POSTGRES_DB}...")
    engine = create_engine(settings.DATABASE_URL)
    
    # 1. Kích hoạt extension vector nếu chưa có
    with Session(engine) as session:
        print("Đảm bảo extension pgvector được kích hoạt...")
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()
    
    # 2. Drop toàn bộ các bảng trong database phát triển
    print("🧹 Đang thực hiện xoá SẠCH toàn bộ bảng cũ trong cơ sở dữ liệu...")
    try:
        # Dùng SQL raw để drop tất cả bảng có CASCADE đề phòng trường hợp khóa ngoại phức tạp
        with Session(engine) as session:
            tables = ["citations", "document_chunks", "summaries", "qa_history", "documents", "notebooks", "notifications", "users"]
            for table in tables:
                session.exec(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            session.commit()
        print("Đã xoá thành công toàn bộ các bảng cũ.")
    except Exception as e:
        print(f"❌ Lỗi khi xoá bảng: {e}")
        return
            
    # 3. Tạo lại toàn bộ các bảng bằng SQLModel
    print("🛠️ Đang tạo lại toàn bộ cấu trúc bảng mới nhất...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Khởi tạo cơ sở dữ liệu mới hoàn toàn sạch sẽ thành công!")
    except Exception as e:
        print(f"Lỗi khi tạo lại cơ sở dữ liệu: {e}")

if __name__ == "__main__":
    reset_entire_database()
