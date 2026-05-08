"""Docker service helpers: detection, lifecycle, cleanup."""
import grp
import os
import shutil

from awesome_welcome.helpers import run_command


DOCKER_UNIT = "docker.service"


def docker_needs_sudo():
    """Return True if invoking the docker CLI requires sudo for this user.

    /var/run/docker.sock is owned by root and the `docker` group; non-root
    users can talk to dockerd directly only if they are members of that
    group (and have re-logged in since being added). We check the active
    supplementary groups via os.getgroups() so the result reflects the
    current process's actual capability — not just /etc/group membership
    that hasn't taken effect yet.
    """
    try:
        if os.geteuid() == 0:
            return False
    except AttributeError:
        pass
    try:
        docker_grp = grp.getgrnam("docker")
    except KeyError:
        return True
    try:
        active_groups = set(os.getgroups())
    except OSError:
        active_groups = set()
    return docker_grp.gr_gid not in active_groups


def _docker_prefix():
    """Return 'sudo ' or '' depending on whether docker access needs sudo."""
    return "sudo " if docker_needs_sudo() else ""


def detect_docker_installed():
    """Detect Docker installation by binary presence and the systemd unit."""
    if not shutil.which("docker"):
        return False
    code, out, _ = run_command(["systemctl", "list-unit-files", DOCKER_UNIT])
    return code == 0 and DOCKER_UNIT in out


def docker_install_command():
    """Install Docker + Compose and enable the service."""
    return (
        "sudo pacman -S --needed --noconfirm docker docker-compose && "
        "sudo systemctl enable --now docker"
    )


def docker_reinstall_command():
    """Reinstall/repair Docker + Compose packages."""
    return (
        "sudo pacman -S --noconfirm docker docker-compose && "
        "sudo systemctl enable docker && "
        "sudo systemctl restart docker"
    )


def docker_start_command():
    return "sudo systemctl start docker"


def docker_stop_command():
    return "sudo systemctl stop docker"


def docker_restart_command():
    return "sudo systemctl restart docker"


def docker_prune_command():
    """Cleanup unused Docker stuff: stopped containers, dangling images, unused networks, build cache.

    Prefixes with sudo only when needed: /var/run/docker.sock is gated on the
    `docker` group, so users in that group can run the command directly.
    Without sudo on a non-member account, the command fails with
    `permission denied while trying to connect to the docker API at
    unix:///var/run/docker.sock`.
    """
    return f"{_docker_prefix()}docker system prune -f"


def docker_prune_images_command():
    """Cleanup unused Docker stuff + unused images.

    Prefixes with sudo only when needed (see docker_prune_command).
    """
    return f"{_docker_prefix()}docker system prune -a -f"


def docker_prune_volumes_command():
    """Cleanup unused Docker stuff + unused images + unused volumes (DESTRUCTIVE).

    Prefixes with sudo only when needed (see docker_prune_command).
    """
    return f"{_docker_prefix()}docker system prune -a --volumes -f"
