import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import OpsgenieClient
from .config import Settings

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
_gateway_creds_var: contextvars.ContextVar[tuple[str, str] | None] = contextvars.ContextVar(
    "opsgenie_gateway_creds", default=None
)


def get_client_from_context() -> OpsgenieClient | None:
    """Resolve the active OpsgenieClient for the current request context."""
    creds = _gateway_creds_var.get()
    if not creds:
        return None
    api_key, base_url = creds
    return OpsgenieClient(api_key, base_url)


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads X-Opsgenie-Api-Key (required) and X-Opsgenie-Base-Url (optional —
    for EU-instance customers who need https://api.eu.opsgenie.com; defaults
    to settings.opsgenie_base_url otherwise) from request headers and stores
    them in the contextvar. Returns 401 if the API key is missing on /mcp
    requests.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        api_key = request.headers.get("x-opsgenie-api-key")
        if not api_key:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": "This server requires the X-Opsgenie-Api-Key header",
                    "required_headers": ["X-Opsgenie-Api-Key"],
                    "optional_headers": ["X-Opsgenie-Base-Url"],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        base_url = request.headers.get("x-opsgenie-base-url") or self.settings.opsgenie_base_url

        ctx_token = _gateway_creds_var.set((api_key, base_url))
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_creds_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all Opsgenie tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="opsgenie-mcp",
        instructions=(
            "Opsgenie (Atlassian) is an alerting and on-call incident-management "
            "platform: monitoring/observability tools fire alerts into it, and "
            "Opsgenie tracks each alert's lifecycle (open → acknowledged → closed), "
            "routes it to responders, and escalates it if nobody acts in time. "
            "This service exposes the alert-lifecycle operations: "
            "opsgenie_alert_list_alerts / opsgenie_alert_get_alert / "
            "opsgenie_alert_count_alerts for querying; opsgenie_alert_create_alert "
            "for raising a new one; opsgenie_alert_acknowledge_alert, "
            "opsgenie_alert_close_alert, opsgenie_alert_snooze_alert, "
            "opsgenie_alert_escalate_alert_to_next, and opsgenie_alert_assign_alert "
            "for working an alert; opsgenie_alert_add_note_to_alert, "
            "opsgenie_alert_add_tags_to_alert/opsgenie_alert_remove_tags_from_alert, "
            "opsgenie_alert_add_responder_to_alert, and "
            "opsgenie_alert_add_team_to_alert for annotating/routing it; "
            "opsgenie_alert_update_alert_message/description/priority for edits; "
            "opsgenie_alert_list_alert_logs/opsgenie_alert_list_alert_notes for "
            "history; and opsgenie_alert_delete_alert as the one irreversible "
            "operation. Typical flow: opsgenie_alert_list_alerts (or "
            "opsgenie_alert_get_alert with a known identifier) to find the alert, "
            "then act on it by identifier. Alerts can be addressed by id, tinyId, "
            "or alias — pass the matching identifier_type."
        ),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        stateless_http=True,
        json_response=True,
    )

    client_factory: Callable[[], OpsgenieClient | None] = get_client_from_context

    from .tools import (
        alert,
    )

    for mod in (
        alert,
    ):
        mod.register(mcp, client_factory)

    return mcp
