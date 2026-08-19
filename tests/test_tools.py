"""tools/list snapshot + error-envelope mapping tests.

No network calls: tool enumeration goes through FastMCP's in-process
list_tools(), and the error-code mapping is tested directly against
OpsgenieError, independent of any real HTTP request.
"""

import pytest

from opsgenie_mcp.api_client import OpsgenieError
from opsgenie_mcp.config import Settings
from opsgenie_mcp.server import create_mcp_server

# name -> (required params, expected annotation hints)
EXPECTED_TOOLS = {
    "opsgenie_alert_acknowledge_alert": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_add_note_to_alert": ({"identifier", "body"}, set()),
    "opsgenie_alert_add_responder_to_alert": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_add_tags_to_alert": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_add_team_to_alert": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_assign_alert": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_close_alert": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_count_alerts": (set(), {"readOnlyHint"}),
    "opsgenie_alert_create_alert": ({"body"}, set()),
    "opsgenie_alert_delete_alert": ({"identifier"}, {"destructiveHint", "idempotentHint"}),
    "opsgenie_alert_escalate_alert_to_next": ({"identifier", "body"}, set()),
    "opsgenie_alert_get_alert": ({"identifier"}, {"readOnlyHint"}),
    "opsgenie_alert_get_request_status": ({"request_id"}, {"readOnlyHint"}),
    "opsgenie_alert_list_alert_logs": ({"identifier"}, {"readOnlyHint"}),
    "opsgenie_alert_list_alert_notes": ({"identifier"}, {"readOnlyHint"}),
    "opsgenie_alert_list_alerts": (set(), {"readOnlyHint"}),
    "opsgenie_alert_remove_tags_from_alert": (
        {"identifier", "tags"},
        {"destructiveHint", "idempotentHint"},
    ),
    "opsgenie_alert_snooze_alert": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_unacknowledge_alert": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_update_alert_description": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_update_alert_message": ({"identifier", "body"}, {"idempotentHint"}),
    "opsgenie_alert_update_alert_priority": ({"identifier", "body"}, {"idempotentHint"}),
}


@pytest.mark.asyncio
async def test_tools_list_snapshot():
    mcp = create_mcp_server(Settings())
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == set(EXPECTED_TOOLS), f"unexpected tool set: {names}"

    by_name = {t.name: t for t in tools}
    for name, (expected_required, expected_hints) in EXPECTED_TOOLS.items():
        tool = by_name[name]
        required = set(tool.inputSchema.get("required", []))
        assert required == expected_required, f"{name}: required={required}"

        description = tool.description or ""
        assert len(description) <= 500, f"{name}: description too long ({len(description)})"
        first_line = description.strip().splitlines()[0] if description.strip() else ""
        assert len(first_line) <= 100, f"{name}: first line too long: {first_line!r}"
        assert "API:" not in description, f"{name}: leaked implementation detail"
        assert "GET /" not in description and "POST /" not in description, (
            f"{name}: leaked implementation detail"
        )
        assert "DELETE /" not in description and "PUT /" not in description, (
            f"{name}: leaked implementation detail"
        )

        annotations = tool.annotations
        actual_hints = set()
        if annotations is not None:
            for hint in ("readOnlyHint", "destructiveHint", "idempotentHint"):
                if getattr(annotations, hint, None) is True:
                    actual_hints.add(hint)
        assert actual_hints == expected_hints, f"{name}: hints={actual_hints}"


@pytest.mark.asyncio
async def test_service_instructions_present_and_bounded():
    mcp = create_mcp_server(Settings())
    assert mcp.instructions
    assert len(mcp.instructions) <= 1500


@pytest.mark.parametrize(
    "status_code,expected_code,expected_retryable",
    [
        (0, "upstream_error", True),
        (400, "invalid_argument", False),
        (401, "unauthorized", False),
        (403, "unauthorized", False),
        (404, "not_found", False),
        (422, "invalid_argument", False),
        (429, "rate_limited", True),
        (500, "upstream_error", True),
        (503, "upstream_error", True),
    ],
)
def test_error_envelope_mapping(status_code, expected_code, expected_retryable):
    import json

    err = OpsgenieError(status_code, "boom")
    envelope = json.loads(err.to_envelope())
    assert envelope["error"]["code"] == expected_code
    assert envelope["error"]["retryable"] is expected_retryable
    assert envelope["error"]["message"] == "boom"
