import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from backend.app.schemas.schemas import (
    Token, ResetTokenResponse, UserPublic, NotebookResponse, NotificationResponse,
    ChatResponse, SummaryResponse, ChatRequest, NotebookSummarizeRequest, JobResponse, SourceResponse,
)

FIXTURES = json.loads((Path(__file__).resolve().parents[2] / "contracts/phase3.json").read_text(encoding="utf-8"))

@pytest.mark.parametrize("key,schema", [
    ("token", Token), ("reset", ResetTokenResponse), ("user", UserPublic),
    ("notebook", NotebookResponse), ("notification", NotificationResponse),
    ("chat", ChatResponse), ("summary", SummaryResponse), ("job", JobResponse), ("source", SourceResponse),
])
def test_shared_client_contracts(key, schema):
    value = schema.model_validate(FIXTURES[key]).model_dump(mode="json")
    assert set(value) == set(FIXTURES[key])

@pytest.mark.parametrize("model", ["phobert_qa", "xlmroberta_qa"])
def test_qa_models(model):
    assert ChatRequest(question="Question?", model=model).model == model

@pytest.mark.parametrize("schema,payload", [
    (ChatRequest, {"question": "Question?", "model": "xlm_roberta"}),
    (NotebookSummarizeRequest, {"model": "unknown"}),
])
def test_unknown_models_are_rejected(schema, payload):
    with pytest.raises(ValidationError): schema.model_validate(payload)

def test_secret_is_required_and_placeholders_rejected():
    from backend.app.core.config import Settings
    with pytest.raises(ValidationError): Settings(_env_file=None, SECRET_KEY="your-super-secret-key-change-this-in-production")
    with pytest.raises(ValidationError): Settings(_env_file=None, SECRET_KEY="short")
