"""TUI widgets for service and docker management."""
import os
import webbrowser

from textual.widgets import Static, Button, Label
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.app import ComposeResult

from awesome_welcome.models import ServiceType, SERVICE_REGISTRY
from awesome_welcome.helpers import (
    check_systemd_unit_active, check_systemd_unit_enabled,
    check_setup_done, execute_command
)
from awesome_welcome.services.kohya import (
    KOHYA_SESSION, KOHYA_UNIT, KOHYA_USER, KOHYA_DIR
)
from awesome_welcome.services.forge import _forge_extensions_install_command
from awesome_welcome.tui.dialogs import ConfirmDialog


class ServiceWidget(Static):
    """A widget representing one service with controls."""
    def __init__(self, service_type, lang_mgr):
        super().__init__()
        self.service_type = service_type
        self.profile = SERVICE_REGISTRY[service_type]
        self.lang = lang_mgr

    def compose(self) -> ComposeResult:
        with ScrollableContainer(classes="service-panel"):
            yield Horizontal(
                Label(self.lang.t(self.profile.display_name_key), classes="service-title"),
                Label("", id=f"status-{self.service_type.value}", classes="service-status"),
                classes="title-row",
            )
            info_key = f"models_info_{self.service_type.value}"
            info_text = self.lang.t(info_key)
            if info_text != info_key:
                yield Static(info_text, id=f"info-{self.service_type.value}", classes="service-info")
            with Container(classes="button-row"):
                if self.profile.install_cmd:
                    yield Button(self.lang.t("install"), id=f"install-{self.service_type.value}",
                                 tooltip=self.lang.t("tooltip_install"))
                if self.profile.unit_name:
                    yield Button("...", id=f"enable-{self.service_type.value}",
                                 tooltip=self.lang.t("tooltip_enable"))
                    yield Button("...", id=f"start-{self.service_type.value}",
                                 tooltip=self.lang.t("tooltip_start"))
                    yield Button(self.lang.t("restart"), id=f"restart-{self.service_type.value}",
                                 tooltip=self.lang.t("tooltip_restart"))
                if self.service_type == ServiceType.KOHYA:
                    yield Button(self.lang.t("start_gpu"), id="kohya-gpu",
                                 tooltip=self.lang.t("tooltip_kohya_gpu"))
                    yield Button(self.lang.t("start_cpu"), id="kohya-cpu",
                                 tooltip=self.lang.t("tooltip_kohya_cpu"))
                    yield Button(self.lang.t("inspect"), id="kohya-inspect",
                                 tooltip=self.lang.t("tooltip_inspect"))
                if "mc" in self.profile.special_controls and self.profile.path:
                    yield Button(self.lang.t("open_mc"), id=f"mc-{self.service_type.value}",
                                 tooltip=self.lang.t("tooltip_mc"))
                if "extensions" in self.profile.special_controls:
                    yield Button(self.lang.t("install_extensions"), id=f"exts-{self.service_type.value}",
                                 tooltip=self.lang.t("tooltip_extensions"))
                if self.service_type == ServiceType.OLLAMA:
                    yield Button(self.lang.t("open_dockge"), id="open-dockge",
                                 tooltip=self.lang.t("tooltip_open_dockge"))

    def on_mount(self):
        self.update_status()

    def update_status(self):
        status = self.get_status_text()
        self.query_one(f"#status-{self.service_type.value}", Label).update(status)
        info_key = f"models_info_{self.service_type.value}"
        info_text = self.lang.t(info_key)
        if info_text != info_key:
            try:
                self.query_one(f"#info-{self.service_type.value}", Static).update(info_text)
            except Exception:
                pass
        if self.profile.unit_name:
            enabled = check_systemd_unit_enabled(self.profile.unit_name)
            active = check_systemd_unit_active(self.profile.unit_name)
            enable_btn = self.query_one(f"#enable-{self.service_type.value}", Button)
            enable_btn.label = self.lang.t("disable") if enabled else self.lang.t("enable")
            start_btn = self.query_one(f"#start-{self.service_type.value}", Button)
            start_btn.label = self.lang.t("stop") if active else self.lang.t("start")

    def get_status_text(self):
        profile = self.profile
        parts = []
        installed = False
        if profile.path:
            if profile.requires_setup_done:
                installed = check_setup_done(profile.path)
            else:
                installed = os.path.isdir(profile.path)
        else:
            installed = False
        if not installed:
            parts.append(self.lang.t("not_installed"))
        else:
            if profile.unit_name:
                active = check_systemd_unit_active(profile.unit_name)
                enabled = check_systemd_unit_enabled(profile.unit_name)
                parts.append(self.lang.t("status_active") if active else self.lang.t("status_inactive"))
                parts.append(self.lang.t("status_enabled") if enabled else self.lang.t("status_disabled"))
            else:
                parts.append("Installed")
        return " | ".join(parts)

    def on_button_pressed(self, event):
        btn_id = event.button.id
        if btn_id.startswith("install-"):
            svc = btn_id.split("-")[1]
            self.install_service(ServiceType(svc))
        elif btn_id.startswith("enable-"):
            svc = btn_id.split("-")[1]
            self.toggle_enable(ServiceType(svc))
        elif btn_id.startswith("start-"):
            svc = btn_id.split("-")[1]
            self.toggle_start_stop(ServiceType(svc))
        elif btn_id.startswith("restart-"):
            svc = btn_id.split("-")[1]
            self.restart_service(ServiceType(svc))
        elif btn_id == "kohya-gpu":
            self.start_kohya_gpu()
        elif btn_id == "kohya-cpu":
            self.start_kohya_cpu()
        elif btn_id == "kohya-inspect":
            self.inspect_kohya()
        elif btn_id.startswith("mc-"):
            svc = btn_id.split("-")[1]
            self.open_mc(ServiceType(svc))
        elif btn_id.startswith("exts-"):
            self.install_extensions()
        elif btn_id == "open-dockge":
            webbrowser.open("http://localhost:5001")

    def install_service(self, st):
        profile = SERVICE_REGISTRY[st]
        if profile.install_cmd:
            execute_command(profile.install_cmd, f"Installing {profile.key}", tui_app=self.app)

    def toggle_enable(self, st):
        profile = SERVICE_REGISTRY[st]
        if profile.unit_name:
            if check_systemd_unit_enabled(profile.unit_name):
                execute_command(f"sudo systemctl disable --now {profile.unit_name}", f"Disable {profile.key}", tui_app=self.app)
            else:
                execute_command(f"sudo systemctl enable --now {profile.unit_name}", f"Enable {profile.key}", tui_app=self.app)
            self.update_status()

    def toggle_start_stop(self, st):
        profile = SERVICE_REGISTRY[st]
        if profile.unit_name:
            if st == ServiceType.KOHYA:
                if check_systemd_unit_active(profile.unit_name):
                    execute_command(f"sudo systemctl stop {KOHYA_UNIT}; sudo -u {KOHYA_USER} byobu kill-session -t {KOHYA_SESSION}", "Stop Kohya", tui_app=self.app)
                else:
                    env_var = 'export CUDA_VISIBLE_DEVICES="0"'
                    cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
                    execute_command(f"sudo -u {KOHYA_USER} -H bash -c '{cmd}'", "Start Kohya (GPU)", tui_app=self.app)
            else:
                if check_systemd_unit_active(profile.unit_name):
                    execute_command(f"sudo systemctl stop {profile.unit_name}", f"Stop {profile.key}", tui_app=self.app)
                else:
                    execute_command(f"sudo systemctl start {profile.unit_name}", f"Start {profile.key}", tui_app=self.app)
            self.update_status()

    def restart_service(self, st):
        profile = SERVICE_REGISTRY[st]
        if profile.unit_name:
            if st == ServiceType.KOHYA:
                env_var = 'export CUDA_VISIBLE_DEVICES="0"'
                cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
                execute_command(f"sudo systemctl stop {KOHYA_UNIT}; sudo -u {KOHYA_USER} byobu kill-session -t {KOHYA_SESSION}; sleep 2; sudo -u {KOHYA_USER} -H bash -c '{cmd}'", "Restart Kohya", tui_app=self.app)
            else:
                execute_command(f"sudo systemctl restart {profile.unit_name}", f"Restart {profile.key}", tui_app=self.app)
            self.update_status()

    def start_kohya_gpu(self):
        env_var = 'export CUDA_VISIBLE_DEVICES="0"'
        cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
        execute_command(f"sudo -u {KOHYA_USER} -H bash -c '{cmd}'", "Start Kohya GPU", tui_app=self.app)
        self.update_status()

    def start_kohya_cpu(self):
        def run_cpu():
            env_var = 'export CUDA_VISIBLE_DEVICES=""'
            cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
            execute_command(f"sudo -u {KOHYA_USER} -H bash -c '{cmd}'", "Start Kohya CPU", tui_app=self.app)
            self.update_status()

        self.app.push_screen(ConfirmDialog(self.lang.t("cpu_warning_text")), callback=lambda result: run_cpu() if result else None)

    def inspect_kohya(self):
        execute_command(f"echo 'Attaching to Kohya session...'; sleep 3; sudo -u {KOHYA_USER} byobu attach -t {KOHYA_SESSION}", "Inspect Kohya", tui_app=self.app)

    def open_mc(self, st):
        profile = SERVICE_REGISTRY[st]
        if profile.path:
            downloads = os.path.expanduser("~/Downloads")
            execute_command(f"mc {downloads} {profile.path}", f"MC: {profile.key}", tui_app=self.app)

    def install_extensions(self):
        execute_command(_forge_extensions_install_command(), "Install Forge Extensions", tui_app=self.app)


class DockerWidget(Static):
    def __init__(self, lang_mgr):
        super().__init__()
        self.lang = lang_mgr

    def compose(self) -> ComposeResult:
        with Container(classes="service-panel"):
            yield Label(self.lang.t("service_docker"), classes="service-title")
            yield Button(self.lang.t("install_docker"), id="install-docker",
                         tooltip=self.lang.t("tooltip_install_docker"))
            yield Button(self.lang.t("spin_dockge"), id="spin-dockge",
                         tooltip=self.lang.t("tooltip_spin_dockge"))

    def on_button_pressed(self, event):
        if event.button.id == "install-docker":
            execute_command("sudo pacman -S --needed docker docker-compose && sudo systemctl enable --now docker", "Install Docker", tui_app=self.app)
        elif event.button.id == "spin-dockge":
            execute_command("sudo docker compose -f /docker/dockge/docker-compose.yml up -d && sleep 30 && xdg-open http://localhost:5001", "Start Dockge", tui_app=self.app)
