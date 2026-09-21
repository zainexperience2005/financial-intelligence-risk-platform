from unittest.mock import patch

from kit.memory.models import MemorySearchResult
from kit.memory.service import MemoryService


def test_memory_service_remember() -> None:
    service = MemoryService()

    with patch("kit.memory.service.store_memory") as mock_store:
        mock_store.side_effect = lambda record: record

        result = service.remember(
            content="Investigation TX-1006 was flagged.",
            memory_type="investigation",
            retention_days=14,
            metadata={"tx_id": "TX-1006"},
        )

        mock_store.assert_called_once()
        assert result.content == "Investigation TX-1006 was flagged."
        assert result.memory_type == "investigation"
        assert result.expires_at is not None
        assert result.metadata == {"tx_id": "TX-1006"}


def test_memory_service_recall() -> None:
    service = MemoryService()

    fake_results = [
        MemorySearchResult(
            memory_id="mem-1",
            content="Investigation finding",
            memory_type="investigation",
            score=0.88,
        )
    ]

    with patch("kit.memory.service.search_memories", return_value=fake_results):
        results = service.recall("high risk transactions", k=3)
        assert len(results) == 1
        assert results[0].memory_id == "mem-1"
        assert results[0].score == 0.88


def test_memory_service_forget() -> None:
    service = MemoryService()

    with patch("kit.memory.service.delete_memory") as mock_delete:
        service.forget("mem-999")
        mock_delete.assert_called_once_with("mem-999")
