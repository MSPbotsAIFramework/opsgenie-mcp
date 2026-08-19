from .._json import error_envelope

NO_TOKEN = error_envelope(
    "not_configured", "No Opsgenie API key. Send the X-Opsgenie-Api-Key header.", False
)
