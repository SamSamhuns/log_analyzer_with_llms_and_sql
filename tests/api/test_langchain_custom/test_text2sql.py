"""
Test text2sql output parsing helpers.
"""

import pytest

from app.api.langchain_custom.text2sql import _extract_sql_query, _message_to_text


@pytest.mark.parametrize(
    "raw_output, expected",
    [
        ("SELECT ID FROM anomaly_detection_log ORDER BY ID DESC LIMIT 4;", "SELECT ID FROM anomaly_detection_log ORDER BY ID DESC LIMIT 4;"),
        (
            "<think>reasoning</think>\nSELECT ID FROM anomaly_detection_log ORDER BY ID DESC LIMIT 4;",
            "SELECT ID FROM anomaly_detection_log ORDER BY ID DESC LIMIT 4;",
        ),
        (
            "```sql\nSELECT timestamp, prediction FROM anomaly_detection_log LIMIT 5;\n```",
            "SELECT timestamp, prediction FROM anomaly_detection_log LIMIT 5;",
        ),
        (
            '{"SQLQuery":"SELECT log_fid FROM anomaly_detection_log LIMIT 1;"}',
            "SELECT log_fid FROM anomaly_detection_log LIMIT 1;",
        ),
        (
            "<think>Formulating SQL</think>\nSELECT ID FROM anomaly_detection_log LIMIT 3;\nThis query returns latest rows.",
            "SELECT ID FROM anomaly_detection_log LIMIT 3;",
        ),
    ],
)
def test_extract_sql_query(raw_output, expected):
    assert _extract_sql_query(raw_output) == expected


def test_extract_sql_query_raises_on_empty_output():
    with pytest.raises(ValueError, match="empty response"):
        _extract_sql_query("   ")


def test_message_to_text_handles_content_blocks():
    message = {
        "content": [
            {"type": "text", "text": "SELECT"},
            " ID ",
            {"type": "text", "text": "FROM anomaly_detection_log;"},
        ]
    }
    # emulate object-like payload with .content
    class _Msg:
        def __init__(self, payload):
            self.content = payload["content"]

    assert _message_to_text(_Msg(message)) == "SELECT\n ID \nFROM anomaly_detection_log;"
