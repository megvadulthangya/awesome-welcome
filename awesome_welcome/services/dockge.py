"""Dockge container helpers: detection, lifecycle."""
import socket
import urllib.request
import urllib.error

from awesome_welcome.helpers import run_command


DOCKGE_COMPOSE_FILE = "/docker/dockge/docker-compose.yml"
DOCKGE_URL = "http://localhost:5001"
DOCKGE_PORT = 5001


def detect_dockge_running():
    """Detect whether Dockge is reachable on its TCP port.

    Uses a TCP connect to localhost:5001 first (fastest), then falls back to
    an HTTP probe. This avoids needing sudo to query `docker ps` and works
    even when the user's docker socket isn't accessible without elevation.
    """
    try:
        with socket.create_connection(("127.0.0.1", DOCKGE_PORT), timeout=1.0):
            return True
    except (OSError, socket.timeout):
        pass
    try:
        req = urllib.request.Request(DOCKGE_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=2.0):
            return True
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, OSError):
        pass
    return False


def dockge_up_command():
    return (
        f"sudo docker compose -f {DOCKGE_COMPOSE_FILE} up -d && "
        f"sleep 30 && xdg-open {DOCKGE_URL}"
    )


def dockge_stop_command():
    return f"sudo docker compose -f {DOCKGE_COMPOSE_FILE} down"


def dockge_restart_command():
    return f"sudo docker compose -f {DOCKGE_COMPOSE_FILE} restart"


def dockge_open_command():
    return f"xdg-open {DOCKGE_URL}"
