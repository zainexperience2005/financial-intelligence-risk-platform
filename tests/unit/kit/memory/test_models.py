from datetime import UTC, datetime, timedelta

from kit.memory.models import MemoryRecord, MemorySearchResult
from kit.memory.store import is_memory_expired


def test_memory_record_defaults() -> None:
    rec = MemoryRecord(
        content="Test finding content",
        memory_type="investigation",
    )
    assert rec.memory_id is not None
    assert len(rec.memory_id) == 36
    assert rec.content == "Test finding content"
    assert rec.memory_type == "investigation"
    assert rec.expires_at is None
    assert rec.metadata == {}
    assert isinstance(rec.created_at, datetime)


def test_is_memory_expired_with_no_expiration() -> None:
    now = datetime.now(UTC)
    assert not is_memory_expired(None, now)


def test_is_memory_expired_with_past_and_future_dates() -> None:
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)

    assert is_memory_expired(yesterday, now) is True
    assert is_memory_expired(tomorrow, now) is False


def test_memory_search_result_model() -> None:
    result = MemorySearchResult(
        memory_id="mem-123",
        content="Historical investigation context",
        memory_type="summary",
        score=0.92,
        metadata={"source": "unit_test"},
    )
    assert result.memory_id == "mem-123"
    assert result.score == 0.92
    assert result.metadata["source"] == "unit_test"
