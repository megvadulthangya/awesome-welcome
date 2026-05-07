"""Service type definitions and registry."""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class ServiceType(Enum):
    KOHYA = "kohya"
    FORGE = "forge"
    COMFY = "comfy"
    OLLAMA = "ollama"
    DOCKER = "docker"


@dataclass
class ServiceProfile:
    key: str
    display_name_key: str
    path: Optional[str]
    unit_name: Optional[str]
    user: str = "diffusion"
    group: str = "diffusion"
    python_version: Optional[str] = None
    install_cmd: Optional[str] = None
    requires_setup_done: bool = False
    special_controls: List[str] = None

    def __post_init__(self):
        if self.special_controls is None:
            self.special_controls = []


SERVICE_REGISTRY = {
    ServiceType.KOHYA: ServiceProfile(
        key="kohya",
        display_name_key="service_kohya",
        path="/opt/kohya_ss",
        unit_name="kohya_ss.service",
        user="diffusion",
        group="diffusion",
        python_version="3.10",
        install_cmd='cd /opt/kohya_ss && sudo -u diffusion -H ./setup.sh && touch /opt/kohya_ss/.setup_done',
        requires_setup_done=True,
        special_controls=["gpu_cpu", "mc", "inspect"]
    ),
    ServiceType.FORGE: ServiceProfile(
        key="forge",
        display_name_key="service_forge",
        path="/opt/stable-diffusion-webui-forge",
        unit_name="stable-diffusion-webui-forge.service",
        user="diffusion",
        group="diffusion",
        python_version="3.10",
        install_cmd='sudo -u diffusion -g diffusion /bin/bash -c \'cd /opt/stable-diffusion-webui-forge && umask 007 && ./webui.sh && touch /opt/stable-diffusion-webui-forge/.setup_done\'',
        requires_setup_done=True,
        special_controls=["extensions", "mc"]
    ),
    ServiceType.COMFY: ServiceProfile(
        key="comfy",
        display_name_key="service_comfy",
        path="/opt/ComfyUI",
        unit_name="comfyui.service",
        user="diffusion",
        group="diffusion",
        python_version="3.13",
        install_cmd='cd /opt/ComfyUI && sudo -u diffusion -H ./setup.sh && touch /opt/ComfyUI/.setup_done',
        requires_setup_done=True,
        special_controls=["mc"]
    ),
    ServiceType.OLLAMA: ServiceProfile(
        key="ollama",
        display_name_key="service_ollama",
        path="/opt/ollama",
        unit_name="ollama.service",
        user="root",
        group="root",
        install_cmd='curl -fsSL https://ollama.com/install.sh | sh && mkdir -p /opt/ollama && touch /opt/ollama/.setup_done',
        requires_setup_done=True,
        special_controls=[]
    ),
    ServiceType.DOCKER: ServiceProfile(
        key="docker",
        display_name_key="service_docker",
        path=None,
        unit_name="docker.service",
        user="root",
        group="root",
        install_cmd=None,
        requires_setup_done=False,
        special_controls=[]
    ),
}
