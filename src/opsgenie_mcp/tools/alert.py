from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import OpsgenieClient, OpsgenieError
from ._common import NO_TOKEN

# Opsgenie's own documented per-page maximum for these list endpoints is 100
# (stricter than the SOP's 200 fallback ceiling), so we clamp to the
# vendor's real limit rather than the SOP's default.
_MAX_LIMIT = 100

_IDENTIFIER_TYPE_DESC = (
    "Type of the identifier: id, tiny, or alias. Default id. Alias cannot "
    "be used to look up a closed alert."
)


def _clamp_limit(limit: int | None) -> int | None:
    if limit is not None and limit > _MAX_LIMIT:
        return _MAX_LIMIT
    return limit


def register(mcp: FastMCP, client_factory: Callable[[], OpsgenieClient | None]) -> None:
    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_acknowledge_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict,
            Field(
                description=(
                    "Optional fields: user (display name of requester), source, "
                    "note. All optional."
                )
            ),
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Acknowledge an alert, marking it as being worked on."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/acknowledge"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool()
    async def opsgenie_alert_add_note_to_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict,
            Field(description="Fields: note (required text to add), user, source. Optional."),
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Add a note to an alert. Each call appends a new note (not idempotent)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/notes"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_add_responder_to_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict,
            Field(
                description=(
                    "Fields: responder (required — {id|name, type: user/team/"
                    "escalation/schedule}), user, source, note. See Opsgenie docs "
                    "for exact shape."
                )
            ),
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Add a responder (user, team, escalation, or schedule) to an alert."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/responders"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_add_tags_to_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict, Field(description="Fields: tags (required list of strings), user, source, note.")
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Add one or more tags to an alert."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/tags"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_add_team_to_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict,
            Field(description="Fields: team (required — {id} or {name}), user, source, note."),
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Add a team as a responder to an alert."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/teams"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_assign_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict,
            Field(
                description="Fields: owner (required — {id|username} of the new assignee), user, source, note."
            ),
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Assign an alert to a specific user (its sole owner)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/assign"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_close_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[dict, Field(description="Optional fields: user, source, note.")],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Close an alert, ending its active lifecycle."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/close"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def opsgenie_alert_count_alerts(
        query: Annotated[
            str | None, Field(description="Opsgenie search query to filter alerts.")
        ] = None,
        search_identifier: Annotated[
            str | None, Field(description="ID or name of a saved search to apply instead.")
        ] = None,
        search_identifier_type: Annotated[
            str | None, Field(description="Type of search_identifier: id or name. Default id.")
        ] = None,
    ) -> str:
        """Count alerts matching a search query or saved search."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "query": query,
            "searchIdentifier": search_identifier,
            "searchIdentifierType": search_identifier_type,
        }
        try:
            result = await client.get("/v2/alerts/count", params=params)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool()
    async def opsgenie_alert_create_alert(
        body: Annotated[
            dict,
            Field(
                description=(
                    "Fields: message (required, max 130 chars), alias, description, "
                    "responders, visibleTo, actions, tags, details, entity, source, "
                    "priority (P1-P5), user, note. See Opsgenie docs for exact shape."
                )
            ),
        ],
    ) -> str:
        """Create a new alert. Each call raises a distinct alert (not idempotent)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.post("/v2/alerts", params={}, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
    async def opsgenie_alert_delete_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
        user: Annotated[
            str | None, Field(description="Display name of the requester. Max 100 chars.")
        ] = None,
        source: Annotated[
            str | None, Field(description="Display name of the request source. Max 100 chars.")
        ] = None,
    ) -> str:
        """Permanently delete an alert. Irreversible — only call with a confirmed ID."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}"
        params = {"identifierType": identifier_type, "user": user, "source": source}
        try:
            result = await client.delete(path, params=params)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool()
    async def opsgenie_alert_escalate_alert_to_next(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict,
            Field(
                description=(
                    "Fields: escalation (required — {id} or {name} of the escalation "
                    "to advance), user, source, note."
                )
            ),
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Escalate an alert to the next level of its escalation policy."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/escalate"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def opsgenie_alert_get_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Get full details of a single alert by its identifier."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}"
        params = {"identifierType": identifier_type}
        try:
            result = await client.get(path, params=params)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def opsgenie_alert_get_request_status(
        request_id: Annotated[
            str, Field(description="Request UUID returned by an earlier async alert action.")
        ],
    ) -> str:
        """Check the async processing status of a previously submitted alert request."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/requests/{request_id}"
        try:
            result = await client.get(path, params={})
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def opsgenie_alert_list_alert_logs(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
        offset: Annotated[
            str | None, Field(description="Pagination cursor: starting offset value.")
        ] = None,
        direction: Annotated[
            str | None, Field(description="Page direction from offset: next or prev. Default next.")
        ] = None,
        limit: Annotated[
            int | None,
            Field(ge=1, le=_MAX_LIMIT, description="Max log entries to return. Default 20, max 100."),
        ] = None,
        order: Annotated[
            str | None, Field(description="Sort order: desc or asc. Default desc.")
        ] = None,
    ) -> str:
        """List an alert's audit log entries (status/ownership/field changes)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/logs"
        params = {
            "identifierType": identifier_type,
            "offset": offset,
            "direction": direction,
            "limit": _clamp_limit(limit),
            "order": order,
        }
        try:
            result = await client.get(path, params=params)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def opsgenie_alert_list_alert_notes(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
        offset: Annotated[
            str | None, Field(description="Pagination cursor: starting offset value.")
        ] = None,
        direction: Annotated[
            str | None, Field(description="Page direction from offset: next or prev. Default next.")
        ] = None,
        limit: Annotated[
            int | None,
            Field(ge=1, le=_MAX_LIMIT, description="Max notes to return. Default 20, max 100."),
        ] = None,
        order: Annotated[
            str | None, Field(description="Sort order: desc or asc. Default desc.")
        ] = None,
    ) -> str:
        """List the notes that have been added to an alert."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/notes"
        params = {
            "identifierType": identifier_type,
            "offset": offset,
            "direction": direction,
            "limit": _clamp_limit(limit),
            "order": order,
        }
        try:
            result = await client.get(path, params=params)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def opsgenie_alert_list_alerts(
        query: Annotated[
            str | None, Field(description="Opsgenie search query to filter alerts.")
        ] = None,
        search_identifier: Annotated[
            str | None, Field(description="ID or name of a saved search to apply instead.")
        ] = None,
        search_identifier_type: Annotated[
            str | None, Field(description="Type of search_identifier: id or name. Default id.")
        ] = None,
        offset: Annotated[
            str | None, Field(description="Pagination start index. Default 0.")
        ] = None,
        limit: Annotated[
            int | None,
            Field(ge=1, le=_MAX_LIMIT, description="Max alerts to return. Default 20, max 100."),
        ] = None,
        sort: Annotated[
            str | None,
            Field(
                description=(
                    "Field to sort by, e.g. createdAt (default), updatedAt, tinyId, "
                    "message, status, priority, count, lastOccurredAt."
                )
            ),
        ] = None,
        order: Annotated[
            str | None, Field(description="Sort order: desc or asc. Default desc.")
        ] = None,
    ) -> str:
        """List alerts, optionally filtered by a search query or saved search."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "query": query,
            "searchIdentifier": search_identifier,
            "searchIdentifierType": search_identifier_type,
            "offset": offset,
            "limit": _clamp_limit(limit),
            "sort": sort,
            "order": order,
        }
        try:
            result = await client.get("/v2/alerts", params=params)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
    async def opsgenie_alert_remove_tags_from_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        tags: Annotated[
            str, Field(description="Comma-separated tags to remove. Max 20 tags x 50 chars.")
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
        user: Annotated[
            str | None, Field(description="Display name of the requester. Max 100 chars.")
        ] = None,
        source: Annotated[
            str | None, Field(description="Display name of the request source. Max 100 chars.")
        ] = None,
        note: Annotated[
            str | None, Field(description="Additional note to add. Max 25000 chars.")
        ] = None,
    ) -> str:
        """Remove one or more tags from an alert."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/tags"
        params = {
            "tags": tags,
            "identifierType": identifier_type,
            "user": user,
            "source": source,
            "note": note,
        }
        try:
            result = await client.delete(path, params=params)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_snooze_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict,
            Field(
                description=(
                    "Fields: endTime (required ISO-8601 timestamp to snooze until), "
                    "user, source, note."
                )
            ),
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Snooze an alert so it stops notifying until a given time."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/snooze"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_unacknowledge_alert(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[dict, Field(description="Optional fields: user, source, note.")],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Revert a previously acknowledged alert back to unacknowledged."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/unacknowledge"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_update_alert_description(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[dict, Field(description="Fields: description (required new text).")],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Replace an alert's description text."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/description"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_update_alert_message(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[dict, Field(description="Fields: message (required new text, max 130 chars).")],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Replace an alert's message (title) text."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/message"
        params = {"identifierType": identifier_type}
        try:
            result = await client.post(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
    async def opsgenie_alert_update_alert_priority(
        identifier: Annotated[str, Field(description="ID, tiny ID, or alias of the alert.")],
        body: Annotated[
            dict, Field(description="Fields: priority (required, one of P1-P5).")
        ],
        identifier_type: Annotated[str | None, Field(description=_IDENTIFIER_TYPE_DESC)] = None,
    ) -> str:
        """Change an alert's priority level (P1 highest to P5 lowest)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        path = f"/v2/alerts/{identifier}/priority"
        params = {"identifierType": identifier_type}
        try:
            result = await client.put(path, params=params, json_body=body)
            return dump_json_capped(result)
        except OpsgenieError as e:
            return e.to_envelope()
