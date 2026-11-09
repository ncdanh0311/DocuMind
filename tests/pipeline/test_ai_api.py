from fastapi.testclient import TestClient
from ai.main import app
from ai.runtime.registry import ModelRegistry
from ai.runtime.models import runtime


def test_ai_health_and_missing_models_never_trigger_downloads(tmp_path, monkeypatch):
    registry = ModelRegistry(tmp_path)
    monkeypatch.setattr('ai.main.registry', registry)
    monkeypatch.setattr(runtime, 'registry', registry)
    with TestClient(app) as client:
        assert client.get('/health').status_code == 200
        capabilities = client.get('/capabilities').json()['models']
        assert len(capabilities) == 6 and all(not m['ready'] for m in capabilities)
        for endpoint, payload in [
            ('/embed', {'texts': ['test']}),
            ('/split', {'text': 'test', 'model': 'vit5'}),
            ('/qa', {'passages': [{'chunk_id': 'a', 'content': 'test'}], 'question': 'Where?'}),
            ('/summarize', {'text': 'test'}),
        ]:
            response = client.post(endpoint, json=payload)
            assert response.status_code == 503, response.text
        assert client.post('/qa', json={'context': 'legacy', 'question': 'Where?'}).status_code == 422
    assert not list(tmp_path.iterdir())
