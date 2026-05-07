"""Kohya_ss service lifecycle management."""
import time
import subprocess

from awesome_welcome.helpers import run_command

KOHYA_SESSION = "kohya_ss"
KOHYA_UNIT = "kohya_ss.service"
KOHYA_USER = "diffusion"
KOHYA_DIR = "/opt/kohya_ss"


def stop_kohya_session():
    """Stop systemd unit and kill byobu session for Kohya (like Bash)."""
    run_command(["sudo", "systemctl", "stop", KOHYA_UNIT])
    run_command(["sudo", "-u", KOHYA_USER, "byobu", "kill-session", "-t", KOHYA_SESSION])


def start_kohya_session(mode="gpu"):
    """Start Kohya in a byobu session exactly as Bash does."""
    stop_kohya_session()
    time.sleep(1)

    if mode == "cpu":
        env_var = 'export CUDA_VISIBLE_DEVICES=""'
    else:
        env_var = 'export CUDA_VISIBLE_DEVICES="0"'

    cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
    run_command(["sudo", "-u", KOHYA_USER, "-H", "bash", "-c", cmd])


def inspect_kohya_session():
    """Attach to the Kohya byobu session (like Bash)."""
    print("Attaching to Kohya terminal in 3 seconds... Press Ctrl+A then D to detach.")
    time.sleep(3)
    subprocess.run(["sudo", "-u", KOHYA_USER, "byobu", "attach", "-t", KOHYA_SESSION])


def restart_kohya_session(mode="gpu"):
    stop_kohya_session()
    time.sleep(2)
    start_kohya_session(mode)
