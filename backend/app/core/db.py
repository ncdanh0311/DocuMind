from sqlmodel import create_engine, Session, SQLModel
from backend.app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

from sqlalchemy import text

def init_db():
    with Session(engine) as session:
        # Kích hoạt extension vector cho AI
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()
    
    # Tạo các bảng
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
