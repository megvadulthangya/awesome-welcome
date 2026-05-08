"""Docker service helpers: detection, lifecycle, cleanup."""
import shutil

from awesome_welcome.helpers import run_command


DOCKER_UNIT = "docker.service"


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

    Uses sudo because the docker socket usually requires root or membership in
    the `docker` group. Without sudo the command fails with
    `permission denied while trying to connect to the docker API at
    unix:///var/run/docker.sock` on systems where the user hasn't been added
    to the docker group.
    """
    return "sudo docker system prune -f"


def docker_prune_images_command():
    """Cleanup unused Docker stuff + unused images.

    Uses sudo for the same reason as docker_prune_command.
    """
    return "sudo docker system prune -a -f"


def docker_prune_volumes_command():
    """Cleanup unused Docker stuff + unused images + unused volumes (DESTRUCTIVE).

    Uses sudo for the same reason as docker_prune_command.
    """
    return "sudo docker system prune -a --volumes -f"
