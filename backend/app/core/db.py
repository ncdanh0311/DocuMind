from sqlmodel import create_engine, Session, SQLModel
from backend.app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

def init_db():
    # Trong môi trường thực tế, chúng ta thường dùng Alembic cho migrations.
    # Ở đây, tôi sẽ dùng SQLModel.metadata.create_all để tạo bảng nhanh cho bạn.
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
