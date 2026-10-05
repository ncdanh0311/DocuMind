from sqlmodel import create_engine, Session, SQLModel
from backend.app.core.config import settings
from sqlalchemy import text

# Tạo engine với connection pool an toàn và pre-ping
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

def init_db():
    # 1. Kích hoạt extension vector nếu có thể
    try:
        with Session(engine) as session:
            session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
            session.commit()
            print("pgvector extension ready.")
    except Exception as e:
        print(f"Notice: pgvector extension creation bypassed: {e}")

    # 2. Tạo toàn bộ bảng SQLModel
    try:
        SQLModel.metadata.create_all(engine)
        print("All SQLModel tables created successfully.")
    except Exception as e:
        print(f"Error creating full SQLModel tables: {e}")
        # Fallback: Tạo các bảng cốt lõi không phụ thuộc pgvector trước
        try:
            from backend.app.models.models import User, Notebook, Notification, Summary, QAHistory, Document
            for model in [User, Notebook, Document, Notification, Summary, QAHistory]:
                try:
                    model.metadata.create_all(engine, tables=[model.__table__])
                    print(f"Created core table: {model.__tablename__}")
                except Exception as me:
                    print(f"Could not create table {model.__tablename__}: {me}")
        except Exception as fe:
            print(f"Fallback creation failed: {fe}")

def get_session():
    with Session(engine) as session:
        yield session
