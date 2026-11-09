from typing import Annotated, Literal, Optional
import uuid
from datetime import datetime
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, field_validator

def validate_password(value: str) -> str:
    if len(value) < 8 or len(value.encode("utf-8")) > 72:
        raise ValueError("Password must contain at least 8 characters and at most 72 UTF-8 bytes")
    return value

NewPassword = Annotated[str, AfterValidator(validate_password)]
QAModel = Literal["phobert_qa", "xlmroberta_qa"]
SummaryModel = Literal["vit5", "bartpho"]
NotebookCategory = Literal["study", "project", "research", "personal"]

class EmailRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.casefold()

class UserCreate(EmailRequest):
    password: NewPassword
    full_name: Optional[str] = None

class UserLogin(EmailRequest):
    password: str

class Token(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    full_name: Optional[str] = None
    avatar_id: Optional[str] = None

class TokenData(BaseModel):
    user_id: Optional[str] = None

class UserPublic(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ForgotPassword(EmailRequest):
    pass

class ResetPassword(BaseModel):
    token: str
    new_password: NewPassword

class VerifyOTP(EmailRequest):
    otp_code: str = Field(pattern=r"^\d{6}$")

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_id: Optional[str] = None

class SecurityUpdate(BaseModel):
    old_password: str
    new_password: NewPassword

class DocumentChunkResponse(BaseModel):
    docuchunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    page_number: Optional[int] = None
    version: int = 0
    global_index: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    page_end: Optional[int] = None
    section_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class NotificationResponse(BaseModel):
    notification_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    body: str
    is_read: bool
    type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    model: QAModel = "phobert_qa"

class CitationResponse(BaseModel):
    id: int
    source_title: str
    page_number: Optional[int] = None
    snippet: str
    document_id: uuid.UUID
    version: int
    start_offset: int
    end_offset: int
    page_end: Optional[int] = None
    section_path: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    status: Literal["answered", "no_answer"] = "answered"
    model_version: Optional[str] = None
    sources: list[str] = []
    citations: list[CitationResponse] = []

class NotebookSummarizeRequest(BaseModel):
    model: SummaryModel = "vit5"



class ResetTokenResponse(BaseModel):
    reset_token: str

class MessageResponse(BaseModel):
    message: str

class ResetPasswordResponse(Token):
    message: str

class NotebookCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    category: NotebookCategory = "personal"
    description: str = Field(default="", max_length=1000)
    is_private: bool = True
    show_on_home: bool = True
    icon_path: Optional[str] = Field(default=None, max_length=512)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be blank")
        return value

class NotebookUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category: Optional[NotebookCategory] = None
    description: Optional[str] = Field(default=None, max_length=1000)
    is_private: Optional[bool] = None
    show_on_home: Optional[bool] = None
    icon_path: Optional[str] = Field(default=None, max_length=512)

    @field_validator("category")
    @classmethod
    def category_cannot_be_null(cls, value):
        if value is None: raise ValueError("Category cannot be null")
        return value

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Title cannot be blank")
        return value

class NotebookResponse(NotebookCreate):
    model_config = ConfigDict(from_attributes=True)
    notebook_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    document_count: int = 0

class SummaryResponse(BaseModel):
    summary_id: uuid.UUID
    job_id: uuid.UUID
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    summary: Optional[str] = None
    model: SummaryModel
    model_version: str
    coverage: float = Field(default=0, ge=0, le=1)
    processed_units: int = Field(default=0, ge=0)
    total_units: int = Field(default=0, ge=0)
    error_code: Optional[str] = None
    stale: bool = False

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: uuid.UUID
    kind: Literal["ingest", "summarize"]
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    progress: float = Field(ge=0, le=1)
    attempt: int = Field(ge=0)
    error_code: Optional[str] = None

class SourceResponse(BaseModel):
    document_id: uuid.UUID
    version: int
    start_offset: int
    end_offset: int
    text: str
    sections: list[dict]


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    document_id: uuid.UUID
    notebook_id: uuid.UUID
    file_name: str
    status: str
    uploaded_at: datetime
    current_version: int = 0
    error_code: Optional[str] = None
    job_id: Optional[uuid.UUID] = None

class DocumentRenameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value or any(c in value for c in '/\\') or any(ord(c) < 32 for c in value):
            raise ValueError("Invalid document title")
        return value
