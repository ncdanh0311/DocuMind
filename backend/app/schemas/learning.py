import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceInput(BaseModel):
    document_id: uuid.UUID
    version: int = Field(ge=1)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=1)
    snippet: str | None = Field(default=None, max_length=20000)


class CardCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=10000)
    source: SourceInput | None = None

    @field_validator("question", "answer")
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError("Must not be blank")
        return value.strip()


class CardUpdate(CardCreate):
    expected_revision: int = Field(ge=1)


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: uuid.UUID
    grade: Literal["again", "remembered"]
    expected_revision: int = Field(ge=0)
    card_revision: int = Field(ge=1)


class ReviewResponse(BaseModel):
    card_id: uuid.UUID
    stage: int
    revision: int
    due_at: datetime
    last_review_at: datetime | None


class CardSource(SourceInput):
    snippet: str
    source_title: str
    page_number: int | None = None
    page_end: int | None = None
    section_path: str | None = None
    source_state: Literal["available", "changed", "missing"]


class CardResponse(BaseModel):
    card_id: uuid.UUID
    notebook_id: uuid.UUID
    question: str
    answer: str
    source: CardSource | None
    revision: int
    created_at: datetime
    updated_at: datetime
    review: ReviewResponse


class CardPage(BaseModel):
    items: list[CardResponse]
    next_cursor: str | None
