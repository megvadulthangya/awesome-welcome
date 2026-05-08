"""Forge-related service logic: extensions registry and install commands."""

import os

FORGE_EXTENSIONS_DIR = "/opt/stable-diffusion-webui-forge/extensions"

FORGE_EXTENSIONS = [
    {"name": "adetailer", "branch": "main", "url": "https://github.com/Bing-su/adetailer.git"},
    {"name": "DWPose", "branch": "onnx", "url": "https://github.com/IDEA-Research/DWPose.git"},
    {"name": "MyStyleSelectorXL", "branch": "main", "url": "https://github.com/megvadulthangya/MyStyleSelectorXL.git"},
    {"name": "sd-dynamic-prompts", "branch": "main", "url": "https://github.com/adieyal/sd-dynamic-prompts/"},
    {"name": "sd-webui-3d-open-pose-editor", "branch": "main", "url": "https://github.com/nonnonstop/sd-webui-3d-open-pose-editor.git"},
    {"name": "sd-webui-ar-plusplus", "branch": "main", "url": "https://github.com/altoiddealer/--sd-webui-ar-plusplus.git"},
    {"name": "sd-webui-hardware-info-in-metadata", "branch": "master", "url": "https://github.com/light-and-ray/sd-webui-hardware-info-in-metadata.git"},
    {"name": "sd-webui-infinite-image-browsing", "branch": "main", "url": "https://github.com/zanllp/sd-webui-infinite-image-browsing.git"},
    {"name": "stable-diffusion-webui-Prompt_Generator", "branch": "master", "url": "https://github.com/imrayya/stable-diffusion-webui-Prompt_Generator.git"},
    {"name": "Stylez", "branch": "main", "url": "https://github.com/megvadulthangya/Stylez.git"},
    {"name": "ultimate-upscale-for-automatic1111", "branch": "master", "url": "https://github.com/Coyote-A/ultimate-upscale-for-automatic1111.git"},
    {"name": "wildcard-gallery", "branch": "main", "url": "https://github.com/navimixu/wildcard-gallery.git"},
]

# --- Forge Manager constants and helpers ---
FORGE_INSTALL_DIR = "/opt/stable-diffusion-webui-forge"
FORGE_VENV_DIR = f"{FORGE_INSTALL_DIR}/venv"
FORGE_REQ_FILE_OLD = "requirements_versions.txt"
FORGE_REQ_FILE_NEO = "requirements.txt"


def _forge_extensions_install_command(selected_extensions=None):
    """Return shell command to install selected (or all) SD Forge extensions."""
    if selected_extensions is None:
        selected_extensions = FORGE_EXTENSIONS
    cmds = [f"mkdir -p {FORGE_EXTENSIONS_DIR}", f"cd {FORGE_EXTENSIONS_DIR}"]
    for ext in selected_extensions:
        cmds.append(f"git clone -b {ext['branch']} {ext['url']}")
    return " && ".join(cmds)


def detect_forge_flavor():
    """Detect installed forge flavor based on requirements file."""
    if os.path.isfile(os.path.join(FORGE_INSTALL_DIR, FORGE_REQ_FILE_NEO)):
        return "neo"
    elif os.path.isfile(os.path.join(FORGE_INSTALL_DIR, FORGE_REQ_FILE_OLD)):
        return "forge"
    return ""


def forge_python_binary(flavor):
    return "python3.13" if flavor == "neo" else "python3.10"


def forge_requirements_file(flavor):
    if flavor == "neo":
        return f"{FORGE_INSTALL_DIR}/{FORGE_REQ_FILE_NEO}"
    return f"{FORGE_INSTALL_DIR}/{FORGE_REQ_FILE_OLD}"


def forge_rebuild_venv_command(flavor):
    python_bin = forge_python_binary(flavor)
    req_file = forge_requirements_file(flavor)
    return (
        f"sudo -u diffusion rm -rf {FORGE_VENV_DIR} && "
        f"sudo -u diffusion {python_bin} -m venv {FORGE_VENV_DIR} && "
        f"sudo -u diffusion {FORGE_VENV_DIR}/bin/python -m pip install --upgrade pip && "
        f"sudo -u diffusion {FORGE_VENV_DIR}/bin/python -m pip install -r {req_file}"
    )


def forge_pip_refresh_command(flavor):
    req_file = forge_requirements_file(flavor)
    return (
        f"sudo -u diffusion {FORGE_VENV_DIR}/bin/python -m pip install --upgrade pip && "
        f"sudo -u diffusion {FORGE_VENV_DIR}/bin/python -m pip install -r {req_file}"
    )


def forge_purge_command(pkg):
    return f"sudo pacman -R --noconfirm {pkg}; sudo rm -rf {FORGE_INSTALL_DIR}"


def forge_install_package_command(pkg):
    return f"sudo pacman -S --noconfirm {pkg}"


FORGE_PACKAGES = [
    "stable-diffusion-webui-forge-neo-git",
    "stable-diffusion-webui-forge-cu124",
    "stable-diffusion-webui-forge",
]


def detect_forge_package():
    """Detect which pacman package is installed.

    Tries `pacman -Qq` once to enumerate all installed packages, then matches
    against our known package names. Falls back to per-name `pacman -Q` if the
    enumeration fails (e.g. limited PATH in launcher environments).

    Order matters: more specific names (-neo-git, -cu124) are checked first
    so they take precedence over the base "stable-diffusion-webui-forge"
    name in any defensive substring matching.
    """
    import subprocess
    import shutil

    pacman = shutil.which("pacman") or "/usr/bin/pacman"

    try:
        result = subprocess.run(
            [pacman, "-Qq"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            installed = set(result.stdout.split())
            for pkg in FORGE_PACKAGES:
                if pkg in installed:
                    return pkg
    except Exception:
        pass

    for pkg_name in FORGE_PACKAGES:
        try:
            result = subprocess.run(
                [pacman, "-Q", pkg_name], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return pkg_name
        except Exception:
            pass
    return ""
