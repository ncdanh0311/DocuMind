from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlmodel import Field, Relationship, SQLModel, Column
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

def utc_field():
    return Field(default_factory=get_utc_now, sa_type=sa.DateTime(timezone=True))

class User(SQLModel, table=True):
    __tablename__ = "users"
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    hashed_password: str
    created_at: datetime = utc_field()
    
    # Profile & Preferences
    avatar_id: Optional[str] = Field(default="mascot-owl-avatar-circle.png")
    
    # Relationships
    notebooks: List["Notebook"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    notifications: List["Notification"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class AuthSession(SQLModel, table=True):
    __tablename__ = "auth_sessions"
    session_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", ondelete="CASCADE", index=True)
    refresh_hash: str
    expires_at: datetime = Field(sa_type=sa.DateTime(timezone=True))
    revoked_at: Optional[datetime] = Field(default=None, sa_type=sa.DateTime(timezone=True))
    created_at: datetime = utc_field()

class PasswordResetChallenge(SQLModel, table=True):
    __tablename__ = "password_reset_challenges"
    challenge_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", ondelete="CASCADE", index=True)
    otp_hash: str
    otp_expires_at: datetime = Field(sa_type=sa.DateTime(timezone=True))
    attempts: int = Field(default=0)
    otp_consumed_at: Optional[datetime] = Field(default=None, sa_type=sa.DateTime(timezone=True))
    reset_hash: Optional[str] = None
    reset_expires_at: Optional[datetime] = Field(default=None, sa_type=sa.DateTime(timezone=True))
    used_at: Optional[datetime] = Field(default=None, sa_type=sa.DateTime(timezone=True))
    created_at: datetime = utc_field()

class AuthRateLimit(SQLModel, table=True):
    __tablename__ = "auth_rate_limits"
    key: str = Field(primary_key=True)
    count: int = Field(default=0)
    window_started_at: datetime = utc_field()
    last_requested_at: datetime = utc_field()

class Notebook(SQLModel, table=True):
    __tablename__ = "notebooks"
    notebook_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", ondelete="CASCADE", index=True)
    title: str
    category: str = Field(default="personal")
    description: str = Field(default="")
    is_private: bool = Field(default=True)
    show_on_home: bool = Field(default=True)
    icon_path: Optional[str] = Field(default=None)
    created_at: datetime = utc_field()
    
    # Relationships
    user: User = Relationship(back_populates="notebooks")
    documents: List["Document"] = Relationship(back_populates="notebook", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    qa_histories: List["QAHistory"] = Relationship(back_populates="notebook", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Document(SQLModel, table=True):
    __tablename__ = "documents"
    document_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    notebook_id: uuid.UUID = Field(foreign_key="notebooks.notebook_id", ondelete="CASCADE", index=True)
    file_name: str
    status: str = Field(default="processing") # processing | ready | error
    uploaded_at: datetime = utc_field()
    current_version: int = Field(default=0)
    requested_version: int = Field(default=0)
    storage_key: Optional[str] = None
    storage_backend: str = Field(default="local")
    file_size_bytes: Optional[int] = Field(default=None, sa_type=sa.BigInteger)
    text_status: str = Field(default="not_started")
    text_error_code: Optional[str] = None
    checksum: Optional[str] = None
    error_code: Optional[str] = None
    
    # Relationships
    notebook: Notebook = Relationship(back_populates="documents")
    chunks: List["DocumentChunk"] = Relationship(back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    summaries: List["Summary"] = Relationship(back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class DocumentVersion(SQLModel, table=True):
    __tablename__ = "document_versions"
    __table_args__ = (sa.UniqueConstraint("document_id", "version", name="uq_document_version"),)
    version_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="documents.document_id", ondelete="CASCADE", index=True)
    version: int
    canonical_text: str = Field(sa_type=sa.Text)
    sections: list[dict] = Field(default_factory=list, sa_column=Column(sa.JSON, nullable=False))
    checksum: str
    pipeline_version: str
    created_at: datetime = utc_field()

class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"
    __table_args__ = (sa.UniqueConstraint("document_id", "version", "global_index", name="uq_chunk_order"),)
    docuchunk_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="documents.document_id", ondelete="CASCADE", index=True)
    content: str
    # Sử dụng Vector từ pgvector (384 chiều cho multilingual-e5-small)
    embedding: Optional[List[float]] = Field(sa_column=Column(Vector(384)))
    embedding_model: Optional[str] = None
    version: int = Field(default=0)
    global_index: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    page_end: Optional[int] = None
    section_path: Optional[str] = None
    provenance: list[dict] = Field(default_factory=list, sa_column=Column(sa.JSON, nullable=False))
    page_number: Optional[int] = None
    
    # Relationships
    document: Document = Relationship(back_populates="chunks")
    citations: List["Citation"] = Relationship(back_populates="chunk", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Summary(SQLModel, table=True):
    __tablename__ = "summaries"
    summary_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    notebook_id: uuid.UUID = Field(foreign_key="notebooks.notebook_id", ondelete="CASCADE", index=True)
    document_id: Optional[uuid.UUID] = Field(default=None, foreign_key="documents.document_id", ondelete="CASCADE", index=True)
    content: Optional[str] = None
    model_name: str
    model_version: str
    pipeline_version: str
    cache_key: str = Field(unique=True)
    status: str = Field(default="queued")
    source_snapshot: list[dict] = Field(default_factory=list, sa_column=Column(sa.JSON, nullable=False))
    parts: list[dict] = Field(default_factory=list, sa_column=Column(sa.JSON, nullable=False))
    total_units: int = Field(default=0)
    processed_units: int = Field(default=0)
    error_code: Optional[str] = None
    created_at: datetime = utc_field()
    document: Optional[Document] = Relationship(back_populates="summaries")

class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    __table_args__ = (sa.Index("ix_jobs_claim", "status", "available_at", "lease_until"),)
    job_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", ondelete="CASCADE", index=True)
    notebook_id: Optional[uuid.UUID] = Field(default=None, foreign_key="notebooks.notebook_id", ondelete="SET NULL", index=True)
    document_id: Optional[uuid.UUID] = Field(default=None, foreign_key="documents.document_id", ondelete="SET NULL", index=True)
    summary_id: Optional[uuid.UUID] = Field(default=None, foreign_key="summaries.summary_id", ondelete="SET NULL", index=True)
    kind: str
    status: str = Field(default="queued")
    dedupe_key: str = Field(unique=True)
    payload: dict = Field(default_factory=dict, sa_column=Column(sa.JSON, nullable=False))
    attempt: int = Field(default=0)
    max_attempts: int = Field(default=3)
    progress: float = Field(default=0)
    error_code: Optional[str] = None
    lease_token: Optional[uuid.UUID] = None
    lease_until: Optional[datetime] = Field(default=None, sa_type=sa.DateTime(timezone=True))
    available_at: datetime = utc_field()
    created_at: datetime = utc_field()
    updated_at: datetime = utc_field()

class QAHistory(SQLModel, table=True):
    __tablename__ = "qa_history"
    qahistory_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    notebook_id: uuid.UUID = Field(foreign_key="notebooks.notebook_id", ondelete="CASCADE", index=True)
    question: str
    answer: str
    model_name: str
    model_version: Optional[str] = None
    citation_snapshot: list[dict] = Field(default_factory=list, sa_column=Column(sa.JSON, nullable=False))
    created_at: datetime = utc_field()
    
    # Relationships
    notebook: Notebook = Relationship(back_populates="qa_histories")
    citations: List["Citation"] = Relationship(back_populates="qa_history", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Citation(SQLModel, table=True):
    __tablename__ = "citations"
    citation_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    qa_id: uuid.UUID = Field(foreign_key="qa_history.qahistory_id", ondelete="CASCADE", index=True)
    chunk_id: uuid.UUID = Field(foreign_key="document_chunks.docuchunk_id", ondelete="CASCADE", index=True)
    relevance_score: Optional[float] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    
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
    created_at: datetime = utc_field()

    # Relationships
    user: User = Relationship(back_populates="notifications")


class StorageLedger(SQLModel, table=True):
    __tablename__ = "storage_ledger"
    ledger_id: int = Field(default=1, primary_key=True)


class UploadReservation(SQLModel, table=True):
    __tablename__ = "upload_reservations"
    reservation_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", ondelete="CASCADE", index=True)
    storage_key: str = Field(unique=True)
    storage_backend: str
    size_bytes: int = Field(sa_type=sa.BigInteger)
    created_at: datetime = utc_field()


class StorageCleanupTask(SQLModel, table=True):
    __tablename__ = "storage_cleanup_tasks"
    __table_args__ = (sa.UniqueConstraint("storage_backend", "storage_key", name="uq_cleanup_object"),)
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    storage_backend: str
    storage_key: str
    created_at: datetime = utc_field()
    attempts: int = Field(default=0)
