"""Ollama service helpers: detection, install/update/uninstall, configurable WebUI URL."""
import os
import shutil

from awesome_welcome.helpers import run_command
from awesome_welcome.services import webui


DEFAULT_WEBUI_URL = webui.DEFAULT_URLS["ollama"]
USER_CONFIG_DIR = webui.USER_CONFIG_DIR
WEBUI_URL_FILE = webui._file_for("ollama")


def detect_ollama_installed():
    """Detect Ollama installation: requires ollama binary AND adjacent lib/ollama dir.

    Linux install detection per upstream docs:
      - command -v ollama (binary present)
      - $(dirname $(which ollama))/../lib/ollama exists
    """
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        return False
    bin_dir = os.path.dirname(os.path.realpath(ollama_path))
    lib_dir = os.path.normpath(os.path.join(bin_dir, "..", "lib", "ollama"))
    return os.path.isdir(lib_dir)


def ollama_install_command():
    """Run the official installer (also serves as 'update')."""
    return (
        "curl -fsSL https://ollama.com/install.sh | sh && "
        "mkdir -p /opt/ollama && touch /opt/ollama/.setup_done"
    )


def ollama_update_command():
    """Same as install — re-running the install script updates Ollama."""
    return "curl -fsSL https://ollama.com/install.sh | sh"


def ollama_uninstall_command():
    """Full uninstall sequence per upstream docs.

    Steps:
      1. Stop and disable systemd service
      2. Remove unit file
      3. Remove libraries from sibling lib/ollama dir
      4. Remove the binary itself
      5. Remove ollama user/group and downloaded models
    """
    return (
        "sudo systemctl stop ollama; "
        "sudo systemctl disable ollama; "
        "sudo rm -f /etc/systemd/system/ollama.service; "
        "if command -v ollama >/dev/null 2>&1; then "
        "  OLLAMA_BIN=\"$(command -v ollama)\"; "
        "  OLLAMA_LIB_DIR=\"$(dirname \"$OLLAMA_BIN\")/../lib/ollama\"; "
        "  sudo rm -rf \"$OLLAMA_LIB_DIR\"; "
        "  sudo rm -f \"$OLLAMA_BIN\"; "
        "fi; "
        "sudo userdel ollama 2>/dev/null; "
        "sudo groupdel ollama 2>/dev/null; "
        "sudo rm -rf /usr/share/ollama; "
        "sudo rm -rf /opt/ollama"
    )


def get_webui_url():
    """Read configured Ollama WebUI URL, falling back to default."""
    try:
        if os.path.isfile(WEBUI_URL_FILE):
            with open(WEBUI_URL_FILE, "r", encoding="utf-8") as fh:
                url = fh.read().strip()
                if url:
                    return url
    except Exception:
        pass
    return DEFAULT_WEBUI_URL


def set_webui_url(url):
    """Persist Ollama WebUI URL to user config."""
    os.makedirs(USER_CONFIG_DIR, exist_ok=True)
    with open(WEBUI_URL_FILE, "w", encoding="utf-8") as fh:
        fh.write(url.strip() + "\n")
