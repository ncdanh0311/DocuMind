from fastapi.testclient import TestClient
import builtins
from ai.main import app
from ai.runtime.registry import ModelRegistry
from ai.runtime.models import runtime


def test_ai_health_and_missing_models_never_trigger_downloads(tmp_path, monkeypatch):
    original_import = builtins.__import__
    heavy_imports = []
    def no_inference_dependencies(name, *args, **kwargs):
        if name.split('.')[0] in {'torch', 'transformers', 'peft', 'pyvi'}:
            heavy_imports.append(name)
            raise ModuleNotFoundError(f'Inference dependency not installed: {name}')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', no_inference_dependencies)
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
            ('/rerank', {'question': 'Where?', 'passages': ['test']}),
        ]:
            response = client.post(endpoint, json=payload)
            assert response.status_code == 503, f'{endpoint}: {response.text}'
        assert client.post('/qa', json={'context': 'legacy', 'question': 'Where?'}).status_code == 422
    assert not list(tmp_path.iterdir())
    assert heavy_imports == []
