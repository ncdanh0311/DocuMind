from datetime import datetime
from typing import List, Optional
import uuid
from sqlmodel import Field, Relationship, SQLModel, Column
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

class User(SQLModel, table=True):
    __tablename__ = "users"
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # OTP for Password Reset
    otp_code: Optional[str] = None
    otp_expiry: Optional[datetime] = None
    
    # Security & Long-term session
    refresh_token: Optional[str] = None
    refresh_token_expiry: Optional[datetime] = None
    
    # Profile & Preferences
    avatar_id: Optional[str] = Field(default="mascot-owl-avatar-circle.png")
    
    # Relationships
    notebooks: List["Notebook"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    notifications: List["Notification"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Notebook(SQLModel, table=True):
    __tablename__ = "notebooks"
    notebook_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", ondelete="CASCADE")
    title: str
    is_private: bool = Field(default=True)
    show_on_home: bool = Field(default=True)
    icon_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="notebooks")
    documents: List["Document"] = Relationship(back_populates="notebook", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    qa_histories: List["QAHistory"] = Relationship(back_populates="notebook", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Document(SQLModel, table=True):
    __tablename__ = "documents"
    document_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    notebook_id: uuid.UUID = Field(foreign_key="notebooks.notebook_id", ondelete="CASCADE")
    file_name: str
    status: str = Field(default="processing") # processing | ready | error
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    notebook: Notebook = Relationship(back_populates="documents")
    chunks: List["DocumentChunk"] = Relationship(back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    summaries: List["Summary"] = Relationship(back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"
    docuchunk_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="documents.document_id", ondelete="CASCADE")
    content: str
    # Sử dụng Vector từ pgvector (ví dụ 768 chiều cho PhoBERT)
    embedding: Optional[List[float]] = Field(sa_column=Column(Vector(768)))
    embedding_model: Optional[str] = None
    page_number: Optional[int] = None
    
    # Relationships
    document: Document = Relationship(back_populates="chunks")
    citations: List["Citation"] = Relationship(back_populates="chunk", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Summary(SQLModel, table=True):
    __tablename__ = "summaries"
    summary_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="documents.document_id", ondelete="CASCADE")
    content: str
    model_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    document: Document = Relationship(back_populates="summaries")

class QAHistory(SQLModel, table=True):
    __tablename__ = "qa_history"
    qahistory_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    notebook_id: uuid.UUID = Field(foreign_key="notebooks.notebook_id", ondelete="CASCADE")
    question: str
    answer: str
    model_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    notebook: Notebook = Relationship(back_populates="qa_histories")
    citations: List["Citation"] = Relationship(back_populates="qa_history", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Citation(SQLModel, table=True):
    __tablename__ = "citations"
    citation_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    qa_id: uuid.UUID = Field(foreign_key="qa_history.qahistory_id", ondelete="CASCADE")
    chunk_id: uuid.UUID = Field(foreign_key="document_chunks.docuchunk_id", ondelete="CASCADE")
    relevance_score: Optional[float] = None
    
    # Relationships
    qa_history: QAHistory = Relationship(back_populates="citations")
    chunk: DocumentChunk = Relationship(back_populates="citations")

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    notification_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", ondelete="CASCADE", index=True)
    title: str
    body: str
    is_read: bool = Field(default=False)
    type: str = Field(default="info") # success | info | warning | welcome
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="notifications")
