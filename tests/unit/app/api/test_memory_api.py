from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from kit.memory.models import MemoryRecord, MemorySearchResult

client = TestClient(app)


def test_api_remember_endpoint() -> None:
    fake_record = MemoryRecord(
        memory_id="test-mem-1",
        content="Investigation note.",
        memory_type="investigation",
        metadata={"source": "explicit_api"},
    )

    with patch("app.api.memory.memory_service.remember", return_value=fake_record):
        response = client.post(
            "/memory",
            json={
                "content": "Investigation note.",
                "retention_days": 30,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["memory_id"] == "test-mem-1"
        assert data["content"] == "Investigation note."


def test_api_recall_endpoint() -> None:
    fake_results = [
        MemorySearchResult(
            memory_id="test-mem-1",
            content="Investigation note.",
            memory_type="investigation",
            score=0.91,
            metadata={"source": "test"},
        )
    ]

    with patch("app.api.memory.memory_service.recall", return_value=fake_results):
        response = client.post(
            "/memory/recall",
            json={
                "query": "Investigation",
                "k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["memory_id"] == "test-mem-1"
        assert data[0]["score"] == 0.91


def test_api_forget_endpoint() -> None:
    with patch("app.api.memory.memory_service.forget") as mock_forget:
        response = client.delete("/memory/test-mem-1")

        assert response.status_code == 200
        assert response.json() == {
            "deleted": True,
            "memory_id": "test-mem-1",
        }
        mock_forget.assert_called_once_with("test-mem-1")
