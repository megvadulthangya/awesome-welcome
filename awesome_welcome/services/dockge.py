"""Dockge container helpers: detection, lifecycle."""
from awesome_welcome.helpers import run_command


DOCKGE_COMPOSE_FILE = "/docker/dockge/docker-compose.yml"
DOCKGE_URL = "http://localhost:5001"


def detect_dockge_running():
    """Detect whether the Dockge container is currently running."""
    code, out, _ = run_command([
        "docker", "ps", "--filter", "name=dockge",
        "--filter", "status=running", "-q"
    ])
    return code == 0 and bool(out.strip())


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
