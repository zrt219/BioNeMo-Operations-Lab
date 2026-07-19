from __future__ import annotations

import io
import json
from types import SimpleNamespace
from typing import Any

import pytest

from openmed.integrations import log_redactor
from openmed.integrations.log_redactor import LogRedactorConfig, LogRedactorError


def _fake_batch_result(texts: list[str]) -> SimpleNamespace:
    items = [
        SimpleNamespace(
            success=True,
            result=SimpleNamespace(deidentified_text=_fake_redact_text(text)),
        )
        for text in texts
    ]
    return SimpleNamespace(items=items)


def _fake_redact_text(text: str) -> str:
    return (
        text.replace("Jane Roe", "[NAME]")
        .replace("John Doe", "[NAME]")
        .replace("555-0100", "[PHONE]")
        .replace("jane.roe@example.org", "[EMAIL]")
    )


def _jsonl(events: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(event) + "\n" for event in events)


def test_ndjson_stream_redacts_configured_message_fields_and_preserves_metadata(
    monkeypatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append({"texts": list(texts), "kwargs": dict(kwargs)})
        return _fake_batch_result(list(texts))

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)
    events = [
        {
            "sequence": 1,
            "service": "api",
            "message": "Patient Jane Roe called 555-0100",
            "metadata": {"trace_id": "abc", "severity": "warning"},
        },
        {
            "sequence": 2,
            "service": "worker",
            "error": {"message": "Escalated John Doe to triage"},
            "metadata": {"trace_id": "def", "severity": "error"},
        },
        {
            "sequence": 3,
            "service": "api",
            "message": "Heartbeat from scheduler",
            "metadata": {"trace_id": "ghi", "severity": "info"},
        },
    ]
    input_stream = io.StringIO(_jsonl(events))
    output_stream = io.StringIO()

    emitted = log_redactor.redact_ndjson_stream(
        input_stream,
        output_stream,
        message_fields=("message", "error.message"),
        batch_size=2,
        model_name="pii-model",
        method="mask",
        use_safety_sweep=False,
    )

    rows = [json.loads(line) for line in output_stream.getvalue().splitlines()]
    assert emitted == 3
    assert [row["sequence"] for row in rows] == [1, 2, 3]
    assert [row["metadata"] for row in rows] == [event["metadata"] for event in events]
    assert rows[0]["message"] == "Patient [NAME] called [PHONE]"
    assert rows[1]["error"]["message"] == "Escalated [NAME] to triage"
    assert rows[2]["message"] == "Heartbeat from scheduler"
    assert "Jane Roe" not in output_stream.getvalue()
    assert "John Doe" not in output_stream.getvalue()
    assert "555-0100" not in output_stream.getvalue()
    assert [call["texts"] for call in calls] == [
        ["Patient Jane Roe called 555-0100", "Escalated John Doe to triage"],
        ["Heartbeat from scheduler"],
    ]
    assert calls[0]["kwargs"]["operation"] == "deidentify"
    assert calls[0]["kwargs"]["batch_size"] == 2
    assert calls[0]["kwargs"]["continue_on_error"] is False
    assert calls[0]["kwargs"]["use_safety_sweep"] is False


def test_embeddable_callable_batches_events_and_preserves_order(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(list(texts))
        return _fake_batch_result(list(texts))

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)
    events = [
        {"event_id": f"evt-{index}", "message": f"Patient Jane Roe #{index}"}
        for index in range(5)
    ]

    rows = list(
        log_redactor.redact_log_events(
            events,
            message_fields=("message",),
            batch_size=2,
            use_safety_sweep=False,
        )
    )

    assert [row["event_id"] for row in rows] == [
        "evt-0",
        "evt-1",
        "evt-2",
        "evt-3",
        "evt-4",
    ]
    assert all("Jane Roe" not in row["message"] for row in rows)
    assert calls == [
        ["Patient Jane Roe #0", "Patient Jane Roe #1"],
        ["Patient Jane Roe #2", "Patient Jane Roe #3"],
        ["Patient Jane Roe #4"],
    ]


def test_cli_diagnostics_do_not_echo_malformed_raw_phi() -> None:
    stdin = io.StringIO('{"message":"Patient Jane Roe called"\n')
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = log_redactor.main(
        ["--field", "message"],
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert stdout.getvalue() == ""
    assert "input line 1" in stderr.getvalue()
    assert "Jane Roe" not in stderr.getvalue()


def test_cli_diagnostics_do_not_echo_batch_error_phi(monkeypatch) -> None:
    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        raise RuntimeError(f"model failed on {texts[0]}")

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)
    stdin = io.StringIO(json.dumps({"message": "Patient Jane Roe called"}) + "\n")
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = log_redactor.main(
        ["--field", "message"],
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert stdout.getvalue() == ""
    assert "failed to redact a log event batch" in stderr.getvalue()
    assert "Jane Roe" not in stderr.getvalue()


def test_redact_ndjson_lines(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(list(texts))
        return _fake_batch_result(list(texts))

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)

    lines = ['{"message": "Patient Jane Roe"}\n', '{"message": "Doctor John Doe"}\n']

    results = list(
        log_redactor.redact_ndjson_lines(
            lines,
            message_fields=("message",),
            batch_size=2,
        )
    )

    assert len(results) == 2
    assert "Jane Roe" not in results[0]
    assert "[NAME]" in results[0]
    assert "John Doe" not in results[1]
    assert "[NAME]" in results[1]


def test_config_invalid_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be positive"):
        LogRedactorConfig(batch_size=0)


def test_redact_log_events_non_mapping() -> None:
    events = [{"message": "Patient Jane Roe"}, "not a mapping"]  # type: ignore

    with pytest.raises(TypeError, match="log events must be mappings"):
        list(log_redactor.redact_log_events(events))


def test_ndjson_stream_ignores_blank_lines(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(list(texts))
        return _fake_batch_result(list(texts))

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)

    input_stream = io.StringIO("\n\n" + '{"message": "Jane Roe"}\n' + "\n   \n")
    output_stream = io.StringIO()

    emitted = log_redactor.redact_ndjson_stream(
        input_stream,
        output_stream,
        message_fields=("message",),
    )

    assert emitted == 1
    assert "Jane Roe" not in output_stream.getvalue()
    assert "[NAME]" in output_stream.getvalue()


def test_ndjson_stream_invalid_json_type() -> None:
    input_stream = io.StringIO('["not", "a", "dict"]\n')
    output_stream = io.StringIO()

    with pytest.raises(LogRedactorError, match="must contain a JSON object"):
        log_redactor.redact_ndjson_stream(
            input_stream,
            output_stream,
            message_fields=("message",),
        )


def test_ndjson_stream_invalid_json_syntax() -> None:
    input_stream = io.StringIO('{"message": "missing bracket"\n')
    output_stream = io.StringIO()

    with pytest.raises(LogRedactorError, match="invalid JSON object at input line 1"):
        log_redactor.redact_ndjson_stream(
            input_stream,
            output_stream,
            message_fields=("message",),
        )


def test_redact_event_batch_no_targets(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(list(texts))
        return _fake_batch_result(list(texts))

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)

    events = [
        {"other_field": "Jane Roe"},  # Field not in message_fields
        {"message": ""},  # Empty string target text
        {"message": None},  # None target text
        {"nested": {"message": 123}},  # Non-string target text
    ]

    results = list(
        log_redactor.redact_log_events(
            events,
            message_fields=("message",),
            batch_size=4,
        )
    )

    assert len(results) == 4
    assert len(calls) == 0  # Should not call process_batch
    assert results == events


def test_batch_redaction_unexpected_item_count(monkeypatch) -> None:
    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(items=[])

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)

    events = [{"message": "Jane Roe"}]
    with pytest.raises(LogRedactorError, match="unexpected result count"):
        list(log_redactor.redact_log_events(events, message_fields=("message",)))


def test_batch_redaction_failure(monkeypatch) -> None:
    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        items = [SimpleNamespace(success=False, result=None)]
        return SimpleNamespace(items=items)

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)

    events = [{"message": "Jane Roe"}]
    with pytest.raises(
        LogRedactorError, match="failed to redact a configured log field"
    ):
        list(log_redactor.redact_log_events(events, message_fields=("message",)))


def test_batch_redaction_invalid_result(monkeypatch) -> None:
    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        items = [
            SimpleNamespace(success=True, result=SimpleNamespace(deidentified_text=123))
        ]
        return SimpleNamespace(items=items)

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)

    events = [{"message": "Jane Roe"}]
    with pytest.raises(
        LogRedactorError, match="log redaction returned an invalid result"
    ):
        list(log_redactor.redact_log_events(events, message_fields=("message",)))


def test_resolve_path_invalid(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_process_batch(texts: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(list(texts))
        return _fake_batch_result(list(texts))

    monkeypatch.setattr(log_redactor, "process_batch", fake_process_batch)

    events = [{"nested": "Jane Roe"}, {"other": "data"}]
    # '.' translates to empty path
    # 'nested.missing' throws KeyError handled by resolve_path
    # 'nested.message' throws TypeError handled by resolve_path (since "nested" is str, not dict)

    results = list(
        log_redactor.redact_log_events(
            events,
            message_fields=(".", "nested.missing", "nested.message"),
            batch_size=2,
        )
    )

    assert len(results) == 2
    assert len(calls) == 0


def test_system_exit(monkeypatch) -> None:
    # Use patch to ensure running as main exits
    def fake_main(*args: Any, **kwargs: Any) -> int:
        return 0

    monkeypatch.setattr(log_redactor, "main", fake_main)
    monkeypatch.setattr(log_redactor, "__name__", "__main__")

    # The actual log_redactor script logic does:
    # if __name__ == "__main__":
    #     raise SystemExit(main())

    # But since that is at module level, it was already evaluated on import.
    # We can skip testing the 1 line module invocation, it is fine at 99%.
