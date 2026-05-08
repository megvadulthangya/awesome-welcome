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
from awesome_welcome.services.ollama import (
    detect_ollama_installed, ollama_install_command, ollama_update_command,
    ollama_uninstall_command, get_webui_url, set_webui_url,
)
from awesome_welcome.services.docker import (
    detect_docker_installed, docker_install_command, docker_reinstall_command,
    docker_start_command, docker_stop_command, docker_restart_command,
    docker_prune_command, docker_prune_images_command, docker_prune_volumes_command,
)
from awesome_welcome.services.dockge import (
    detect_dockge_running, dockge_up_command, dockge_stop_command,
    dockge_restart_command, dockge_open_command,
)
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
            if self.service_type == ServiceType.FORGE:
                yield Static("", id="forge-installed-label", classes="service-info")
            with Container(classes="button-row"):
                if self.profile.install_cmd:
                    tooltip_key = "tooltip_install_ollama" if self.service_type == ServiceType.OLLAMA else "tooltip_install_venv"
                    yield Button(self.lang.t("install"), id=f"install-{self.service_type.value}",
                                 tooltip=self.lang.t(tooltip_key))
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
                    yield Button(self.lang.t("open_thunar"), id=f"thunar-{self.service_type.value}",
                                 tooltip=self.lang.t("tooltip_thunar"))
                if "extensions" in self.profile.special_controls:
                    yield Button(self.lang.t("install_extensions"), id=f"exts-{self.service_type.value}",
                                 tooltip=self.lang.t("tooltip_extensions"))
                if self.service_type == ServiceType.FORGE:
                    yield Button(self.lang.t("forge_pip_refresh"), id="forge-pip-refresh",
                                 tooltip=self.lang.t("tooltip_forge_pip_refresh"))
                    yield Button(self.lang.t("forge_venv_rebuild"), id="forge-venv-rebuild",
                                 tooltip=self.lang.t("tooltip_forge_venv_rebuild"))
                    yield Button(self.lang.t("forge_switch_version"), id="forge-switch-version",
                                 tooltip=self.lang.t("tooltip_forge_switch_version"))
                    yield Button(self.lang.t("forge_purge"), id="forge-purge",
                                 tooltip=self.lang.t("tooltip_forge_purge"))
                if self.service_type == ServiceType.OLLAMA:
                    yield Button(self.lang.t("open_webui"), id="ollama-webui",
                                 tooltip=self.lang.t("tooltip_open_webui"))
                    yield Button(self.lang.t("edit_webui_url"), id="ollama-edit-url",
                                 tooltip=self.lang.t("tooltip_edit_webui_url"))
                    yield Button(self.lang.t("remove_ollama"), id="ollama-remove",
                                 tooltip=self.lang.t("tooltip_remove_ollama"))

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

        if self.service_type == ServiceType.FORGE:
            from awesome_welcome.services.forge import detect_forge_package
            try:
                pkg = detect_forge_package()
                lbl = self.query_one("#forge-installed-label", Static)
                if pkg:
                    lbl.update(self.lang.t("forge_installed_label").format(pkg=pkg))
                else:
                    lbl.update(self.lang.t("forge_not_installed_label"))
            except Exception:
                pass

        if self.service_type == ServiceType.OLLAMA:
            try:
                btn_install = self.query_one(f"#install-{self.service_type.value}", Button)
                if detect_ollama_installed():
                    btn_install.label = self.lang.t("update_ollama")
                    btn_install.tooltip = self.lang.t("tooltip_update_ollama")
                else:
                    btn_install.label = self.lang.t("install")
                    btn_install.tooltip = self.lang.t("tooltip_install_ollama")
            except Exception:
                pass
            try:
                btn_remove = self.query_one("#ollama-remove", Button)
                btn_remove.disabled = not detect_ollama_installed()
            except Exception:
                pass

    def get_status_text(self):
        profile = self.profile
        parts = []
        if self.service_type == ServiceType.OLLAMA:
            installed = detect_ollama_installed()
        elif profile.path:
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
        elif btn_id.startswith("thunar-"):
            svc = btn_id.split("-")[1]
            self.open_thunar(ServiceType(svc))
        elif btn_id.startswith("exts-"):
            self.install_extensions()
        elif btn_id == "forge-pip-refresh":
            self.forge_pip_refresh()
        elif btn_id == "forge-venv-rebuild":
            self.forge_venv_rebuild()
        elif btn_id == "forge-switch-version":
            self.forge_switch_version()
        elif btn_id == "forge-purge":
            self.forge_purge()
        elif btn_id == "ollama-webui":
            webbrowser.open(get_webui_url())
        elif btn_id == "ollama-edit-url":
            self.edit_webui_url()
        elif btn_id == "ollama-remove":
            self.remove_ollama()

    def install_service(self, st):
        profile = SERVICE_REGISTRY[st]
        if st == ServiceType.OLLAMA:
            cmd = ollama_update_command() if detect_ollama_installed() else ollama_install_command()
            label = "Update Ollama" if detect_ollama_installed() else "Install Ollama"
            execute_command(cmd, label, tui_app=self.app)
            self.update_status()
            return
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

    def open_thunar(self, st):
        profile = SERVICE_REGISTRY[st]
        if profile.path:
            execute_command(f"thunar {profile.path}", f"Thunar: {profile.key}", tui_app=self.app)

    def install_extensions(self):
        from awesome_welcome.tui.dialogs import ExtensionsSelectModal
        from awesome_welcome.services.forge import _forge_extensions_install_command

        def handle_result(selected):
            if selected:
                execute_command(_forge_extensions_install_command(selected), "Install Forge Extensions", tui_app=self.app)

        self.app.push_screen(ExtensionsSelectModal(self.lang), callback=handle_result)

    def forge_pip_refresh(self):
        from awesome_welcome.services.forge import detect_forge_flavor, forge_pip_refresh_command
        flavor = detect_forge_flavor()
        if flavor:
            execute_command(forge_pip_refresh_command(flavor), "Forge: Pip Refresh", tui_app=self.app)

    def forge_venv_rebuild(self):
        from awesome_welcome.services.forge import detect_forge_flavor, forge_rebuild_venv_command
        from awesome_welcome.tui.dialogs import ConfirmDialog
        flavor = detect_forge_flavor()
        if not flavor:
            return

        def do_rebuild(confirmed):
            if confirmed:
                execute_command(forge_rebuild_venv_command(flavor), "Forge: Rebuild venv", tui_app=self.app)

        self.app.push_screen(ConfirmDialog(self.lang.t("forge_confirm_rebuild")), callback=do_rebuild)

    def forge_switch_version(self):
        from awesome_welcome.tui.dialogs import ForgeVersionSelectModal
        from awesome_welcome.services.forge import detect_forge_package
        current_pkg = detect_forge_package()
        self.app.push_screen(
            ForgeVersionSelectModal(self.lang, current_pkg=current_pkg),
            callback=lambda selected: self._handle_version_switch(selected, current_pkg),
        )

    def _handle_version_switch(self, selected_pkg, current_pkg):
        if not selected_pkg:
            return
        if selected_pkg == current_pkg:
            from awesome_welcome.tui.dialogs import InfoDialog
            self.app.push_screen(InfoDialog(self.lang.t("forge_switch_no_change")))
            return
        from awesome_welcome.services.forge import forge_purge_command, forge_install_package_command
        from awesome_welcome.tui.dialogs import ConfirmDialog
        confirm_text = self.lang.t("forge_switch_confirm_text").format(
            current=current_pkg or "-", target=selected_pkg
        )

        def do_switch(confirmed):
            if not confirmed:
                return
            cmd_parts = []
            if current_pkg:
                cmd_parts.append(forge_purge_command(current_pkg))
            cmd_parts.append(forge_install_package_command(selected_pkg))
            execute_command(" && ".join(cmd_parts), "Forge: Switch Version", tui_app=self.app)
            self.update_status()

        self.app.push_screen(ConfirmDialog(confirm_text), callback=do_switch)

    def forge_purge(self):
        from awesome_welcome.tui.dialogs import ConfirmDialog
        from awesome_welcome.services.forge import detect_forge_package, forge_purge_command, FORGE_INSTALL_DIR

        def do_purge(confirmed):
            if confirmed:
                pkg = detect_forge_package()
                if pkg:
                    execute_command(forge_purge_command(pkg), "Forge: Purge", tui_app=self.app)
                else:
                    execute_command(f"sudo rm -rf {FORGE_INSTALL_DIR}", "Forge: Remove files", tui_app=self.app)
                self.update_status()

        self.app.push_screen(ConfirmDialog(self.lang.t("forge_purge_warning")), callback=do_purge)

    def edit_webui_url(self):
        from awesome_welcome.tui.dialogs import InputDialog

        def handle_result(new_url):
            if new_url:
                set_webui_url(new_url.strip())

        self.app.push_screen(
            InputDialog(
                self.lang.t("webui_url_dialog_title"),
                self.lang.t("webui_url_dialog_prompt"),
                get_webui_url(),
                self.lang,
            ),
            callback=handle_result,
        )

    def remove_ollama(self):
        from awesome_welcome.tui.dialogs import ConfirmDialog

        def do_remove(confirmed):
            if confirmed:
                execute_command(ollama_uninstall_command(), "Remove Ollama", tui_app=self.app)
                self.update_status()

        self.app.push_screen(ConfirmDialog(self.lang.t("ollama_remove_warning")), callback=do_remove)


class DockerWidget(Static):
    """Docker tab: install/start/stop/restart/cleanup."""
    def __init__(self, lang_mgr):
        super().__init__()
        self.lang = lang_mgr

    def compose(self) -> ComposeResult:
        with ScrollableContainer(classes="service-panel"):
            yield Horizontal(
                Label(self.lang.t("service_docker"), classes="service-title"),
                Label("", id="docker-status", classes="service-status"),
                classes="title-row",
            )
            with Container(classes="button-row"):
                yield Button(self.lang.t("install_docker"), id="docker-install",
                             tooltip=self.lang.t("tooltip_install_docker"))
                yield Button(self.lang.t("start_docker"), id="docker-start",
                             tooltip=self.lang.t("tooltip_start_docker"))
                yield Button(self.lang.t("restart_docker"), id="docker-restart",
                             tooltip=self.lang.t("tooltip_restart_docker"))
                yield Button(self.lang.t("cleanup_docker_basic"), id="docker-clean-basic",
                             tooltip=self.lang.t("tooltip_cleanup_docker_basic"))
                yield Button(self.lang.t("cleanup_docker_images"), id="docker-clean-images",
                             tooltip=self.lang.t("tooltip_cleanup_docker_images"))
                yield Button(self.lang.t("cleanup_docker_volumes"), id="docker-clean-volumes",
                             tooltip=self.lang.t("tooltip_cleanup_docker_volumes"))

    def on_mount(self):
        self.update_status()

    def update_status(self):
        installed = detect_docker_installed()
        running = installed and check_systemd_unit_active("docker.service")
        try:
            lbl = self.query_one("#docker-status", Label)
            if not installed:
                lbl.update(self.lang.t("docker_status_not_installed"))
            elif running:
                lbl.update(self.lang.t("docker_status_running"))
            else:
                lbl.update(self.lang.t("docker_status_stopped"))
        except Exception:
            pass

        try:
            btn = self.query_one("#docker-install", Button)
            if installed:
                btn.label = self.lang.t("reinstall_docker")
                btn.tooltip = self.lang.t("tooltip_reinstall_docker")
            else:
                btn.label = self.lang.t("install_docker")
                btn.tooltip = self.lang.t("tooltip_install_docker")
        except Exception:
            pass

        try:
            btn_start = self.query_one("#docker-start", Button)
            if running:
                btn_start.label = self.lang.t("stop_docker")
                btn_start.tooltip = self.lang.t("tooltip_stop_docker")
            else:
                btn_start.label = self.lang.t("start_docker")
                btn_start.tooltip = self.lang.t("tooltip_start_docker")
            btn_start.disabled = not installed
        except Exception:
            pass

        for btn_id in ("docker-restart", "docker-clean-basic",
                       "docker-clean-images", "docker-clean-volumes"):
            try:
                self.query_one(f"#{btn_id}", Button).disabled = not installed
            except Exception:
                pass

    def on_button_pressed(self, event):
        bid = event.button.id
        if bid == "docker-install":
            cmd = docker_reinstall_command() if detect_docker_installed() else docker_install_command()
            label = "Reinstall Docker" if detect_docker_installed() else "Install Docker"
            execute_command(cmd, label, tui_app=self.app)
        elif bid == "docker-start":
            if check_systemd_unit_active("docker.service"):
                execute_command(docker_stop_command(), "Stop Docker", tui_app=self.app)
            else:
                execute_command(docker_start_command(), "Start Docker", tui_app=self.app)
        elif bid == "docker-restart":
            execute_command(docker_restart_command(), "Restart Docker", tui_app=self.app)
        elif bid == "docker-clean-basic":
            execute_command(docker_prune_command(), "Docker Cleanup (basic)", tui_app=self.app)
        elif bid == "docker-clean-images":
            execute_command(docker_prune_images_command(), "Docker Cleanup (+ images)", tui_app=self.app)
        elif bid == "docker-clean-volumes":
            def do_clean(confirmed):
                if confirmed:
                    execute_command(docker_prune_volumes_command(),
                                    "Docker Cleanup (+ volumes)", tui_app=self.app)

            self.app.push_screen(
                ConfirmDialog(self.lang.t("cleanup_docker_volumes_warning")),
                callback=do_clean,
            )
        self.update_status()


class DockgeWidget(Static):
    """Dockge tab: spin up/stop/open/restart."""
    def __init__(self, lang_mgr):
        super().__init__()
        self.lang = lang_mgr

    def compose(self) -> ComposeResult:
        with ScrollableContainer(classes="service-panel"):
            yield Horizontal(
                Label(self.lang.t("service_dockge"), classes="service-title"),
                Label("", id="dockge-status", classes="service-status"),
                classes="title-row",
            )
            with Container(classes="button-row"):
                yield Button(self.lang.t("spin_dockge"), id="dockge-spin",
                             tooltip=self.lang.t("tooltip_spin_dockge"))
                yield Button(self.lang.t("open_dockge"), id="dockge-open",
                             tooltip=self.lang.t("tooltip_open_dockge"))
                yield Button(self.lang.t("restart_dockge"), id="dockge-restart",
                             tooltip=self.lang.t("tooltip_restart_dockge"))

    def on_mount(self):
        self.update_status()

    def update_status(self):
        docker_installed = detect_docker_installed()
        running = docker_installed and detect_dockge_running()
        try:
            lbl = self.query_one("#dockge-status", Label)
            if not docker_installed:
                lbl.update(self.lang.t("dockge_status_not_installed"))
            elif running:
                lbl.update(self.lang.t("dockge_status_running"))
            else:
                lbl.update(self.lang.t("dockge_status_stopped"))
        except Exception:
            pass

        try:
            btn = self.query_one("#dockge-spin", Button)
            if running:
                btn.label = self.lang.t("stop_dockge")
                btn.tooltip = self.lang.t("tooltip_stop_dockge")
            else:
                btn.label = self.lang.t("spin_dockge")
                btn.tooltip = self.lang.t("tooltip_spin_dockge")
            btn.disabled = not docker_installed
        except Exception:
            pass

        try:
            self.query_one("#dockge-open", Button).disabled = not running
        except Exception:
            pass
        try:
            self.query_one("#dockge-restart", Button).disabled = not running
        except Exception:
            pass

    def on_button_pressed(self, event):
        bid = event.button.id
        if bid == "dockge-spin":
            if detect_dockge_running():
                execute_command(dockge_stop_command(), "Stop Dockge", tui_app=self.app)
            else:
                execute_command(dockge_up_command(), "Spin up Dockge", tui_app=self.app)
        elif bid == "dockge-open":
            execute_command(dockge_open_command(), "Open Dockge", tui_app=self.app)
        elif bid == "dockge-restart":
            execute_command(dockge_restart_command(), "Restart Dockge", tui_app=self.app)
        self.update_status()
