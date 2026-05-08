"""Per-service WebUI URL configuration.

Each AI service has a "main" web UI that the user wants to open in a browser.
The default URLs match the upstream defaults (Forge / Comfy / Kohya bind to
their well-known ports; Ollama's chat UI is the Open WebUI container deployed
through Dockge). Users can override the URL per-service so they can point at
a remote/cloudflared/reverse-proxied hostname instead of localhost.
"""
import os


DEFAULT_URLS = {
    "forge": "http://localhost:7860",
    "comfy": "http://localhost:8188",
    "kohya": "http://localhost:7861",
    "ollama": "http://localhost:8080",
}

USER_CONFIG_DIR = os.path.expanduser("~/.config/awesome-welcome")


def _file_for(service_value):
    return os.path.join(USER_CONFIG_DIR, f"{service_value}_webui_url")


def get_url(service_value):
    """Read the configured WebUI URL for the given service, falling back to default."""
    path = _file_for(service_value)
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                value = fh.read().strip()
                if value:
                    return value
    except Exception:
        pass
    return DEFAULT_URLS.get(service_value, "http://localhost")


def set_url(service_value, url):
    """Persist the WebUI URL for the given service."""
    os.makedirs(USER_CONFIG_DIR, exist_ok=True)
    with open(_file_for(service_value), "w", encoding="utf-8") as fh:
        fh.write(url.strip() + "\n")
