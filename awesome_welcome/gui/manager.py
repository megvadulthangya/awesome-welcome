"""GTK3 AI Services Manager window."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import os
import threading
import time
import webbrowser

from awesome_welcome.config import NORD_COLORS
from awesome_welcome.i18n import STRINGS
from awesome_welcome.models import ServiceType, SERVICE_REGISTRY
from awesome_welcome.helpers import (
    check_systemd_unit_active, check_systemd_unit_enabled,
    check_setup_done, execute_command
)
from awesome_welcome.services.kohya import (
    KOHYA_SESSION, KOHYA_UNIT, KOHYA_USER, KOHYA_DIR
)
from awesome_welcome.services.forge import _forge_extensions_install_command
from awesome_welcome.gui.css import CSS_DATA


class AIServicesManagerGTK(Gtk.Window):
    def __init__(self, parent_welcome=None):
        super().__init__(title=STRINGS["en"]["window_title"])
        self.set_default_size(950, 750)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)

        self.lang = "en"
        self.strings = STRINGS[self.lang]
        self.polling = False
        self.parent_welcome = parent_welcome

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_DATA.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = self.strings["window_title"]
        self.set_titlebar(header)

        self.lang_btn = Gtk.Button(label=self.strings["language"])
        self.lang_btn.set_tooltip_text(self.strings["tooltip_language"])
        self.lang_btn.connect("clicked", self.on_toggle_language)
        header.pack_end(self.lang_btn)

        refresh_btn = Gtk.Button(label=self.strings["refresh"])
        refresh_btn.set_tooltip_text(self.strings["tooltip_refresh"])
        refresh_btn.connect("clicked", lambda x: self.refresh_all())
        header.pack_end(refresh_btn)

        close_btn = Gtk.Button(label=self.strings["close"])
        close_btn.connect("clicked", self.on_close_clicked)
        header.pack_start(close_btn)

        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        self.create_service_tabs()

        self.polling = True
        self.poll_thread = threading.Thread(target=self.poll_services_loop, daemon=True)
        self.poll_thread.start()

        self.show_all()
        self.connect("destroy", self.on_destroy)

    def on_close_clicked(self, btn):
        self.destroy()

    def on_destroy(self, widget):
        self.polling = False
        if self.parent_welcome:
            self.parent_welcome.show()

    def on_toggle_language(self, btn):
        self.lang = "hu" if self.lang == "en" else "en"
        self.strings = STRINGS[self.lang]
        self.set_title(self.strings["window_title"])
        btn.set_label(self.strings["language"])
        btn.set_tooltip_text(self.strings["tooltip_language"])
        self.update_ui_language()

    def update_ui_language(self):
        for i, st in enumerate([ServiceType.KOHYA, ServiceType.FORGE, ServiceType.COMFY, ServiceType.OLLAMA]):
            profile = SERVICE_REGISTRY[st]
            page = self.notebook.get_nth_page(i)
            label = self.notebook.get_tab_label(page)
            label.set_text(self.strings[profile.display_name_key])
        docker_page = self.notebook.get_nth_page(4)
        label = self.notebook.get_tab_label(docker_page)
        label.set_text(self.strings["service_docker"])
        for st in [ServiceType.KOHYA, ServiceType.FORGE, ServiceType.COMFY]:
            info_key = f"models_info_{st.value}"
            if hasattr(self, f"info_label_{st.value}"):
                info_label = getattr(self, f"info_label_{st.value}")
                GLib.idle_add(info_label.set_markup, f"<i>{self.strings[info_key]}</i>")
        self.refresh_all()

    def create_service_tabs(self):
        for st in [ServiceType.KOHYA, ServiceType.FORGE, ServiceType.COMFY, ServiceType.OLLAMA]:
            profile = SERVICE_REGISTRY[st]
            page = self.create_service_page(st, profile)
            label = Gtk.Label(label=self.strings[profile.display_name_key])
            self.notebook.append_page(page, label)

        docker_page = self.create_docker_page()
        label = Gtk.Label(label=self.strings["service_docker"])
        self.notebook.append_page(docker_page, label)

    def create_service_page(self, st, profile):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)

        hbox_title = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_label = Gtk.Label()
        title_label.get_style_context().add_class("service-title")
        title_label.set_text(self.strings[profile.display_name_key])
        hbox_title.pack_start(title_label, False, False, 0)

        status_label = Gtk.Label()
        status_label.get_style_context().add_class("service-status")
        hbox_title.pack_end(status_label, False, False, 0)
        box.pack_start(hbox_title, False, False, 0)

        if st == ServiceType.FORGE:
            info_label = Gtk.Label()
            info_label.set_markup(f"<i>{self.strings['models_info_forge']}</i>")
            info_label.set_line_wrap(True)
            info_label.set_xalign(0)
            info_label.set_margin_top(5)
            info_label.set_margin_bottom(5)
            box.pack_start(info_label, False, False, 0)
            setattr(self, f"info_label_{st.value}", info_label)
        elif st == ServiceType.COMFY:
            info_label = Gtk.Label()
            info_label.set_markup(f"<i>{self.strings['models_info_comfy']}</i>")
            info_label.set_line_wrap(True)
            info_label.set_xalign(0)
            info_label.set_margin_top(5)
            info_label.set_margin_bottom(5)
            box.pack_start(info_label, False, False, 0)
            setattr(self, f"info_label_{st.value}", info_label)
        elif st == ServiceType.KOHYA:
            info_label = Gtk.Label()
            info_label.set_markup(f"<i>{self.strings['models_info_kohya']}</i>")
            info_label.set_line_wrap(True)
            info_label.set_xalign(0)
            info_label.set_margin_top(5)
            info_label.set_margin_bottom(5)
            box.pack_start(info_label, False, False, 0)
            setattr(self, f"info_label_{st.value}", info_label)

        btn_box = Gtk.FlowBox()
        btn_box.set_selection_mode(Gtk.SelectionMode.NONE)
        btn_box.set_homogeneous(False)
        btn_box.set_column_spacing(5)
        btn_box.set_row_spacing(5)

        if profile.install_cmd:
            btn_install = Gtk.Button(label=self.strings["install"])
            btn_install.get_style_context().add_class("service-button")
            btn_install.set_tooltip_text(self.strings["tooltip_install"])
            btn_install.connect("clicked", self.on_install_clicked, st)
            btn_box.add(btn_install)
            setattr(self, f"btn_install_{st.value}", btn_install)

        if profile.unit_name:
            btn_enable = Gtk.Button(label="...")
            btn_enable.get_style_context().add_class("service-button")
            btn_enable.set_tooltip_text(self.strings["tooltip_enable"])
            btn_enable.connect("clicked", self.on_toggle_enable, st)
            btn_box.add(btn_enable)
            setattr(self, f"btn_enable_{st.value}", btn_enable)

            btn_start = Gtk.Button(label="...")
            btn_start.get_style_context().add_class("service-button")
            btn_start.set_tooltip_text(self.strings["tooltip_start"])
            btn_start.connect("clicked", self.on_toggle_start_stop, st)
            btn_box.add(btn_start)
            setattr(self, f"btn_start_{st.value}", btn_start)

            btn_restart = Gtk.Button(label=self.strings["restart"])
            btn_restart.get_style_context().add_class("service-button")
            btn_restart.set_tooltip_text(self.strings["tooltip_restart"])
            btn_restart.connect("clicked", self.on_restart, st)
            btn_box.add(btn_restart)
            setattr(self, f"btn_restart_{st.value}", btn_restart)

        if st == ServiceType.KOHYA:
            btn_gpu = Gtk.Button(label=self.strings["start_gpu"])
            btn_gpu.get_style_context().add_class("service-button")
            btn_gpu.set_tooltip_text(self.strings["tooltip_kohya_gpu"])
            btn_gpu.connect("clicked", self.on_start_kohya_gpu)
            btn_box.add(btn_gpu)
            self.btn_kohya_gpu = btn_gpu

            btn_cpu = Gtk.Button(label=self.strings["start_cpu"])
            btn_cpu.get_style_context().add_class("service-button")
            btn_cpu.set_tooltip_text(self.strings["tooltip_kohya_cpu"])
            btn_cpu.connect("clicked", self.on_start_kohya_cpu)
            btn_box.add(btn_cpu)
            self.btn_kohya_cpu = btn_cpu

            btn_inspect = Gtk.Button(label=self.strings["inspect"])
            btn_inspect.get_style_context().add_class("service-button")
            btn_inspect.set_tooltip_text(self.strings["tooltip_inspect"])
            btn_inspect.connect("clicked", self.on_inspect_kohya)
            btn_box.add(btn_inspect)
            self.btn_kohya_inspect = btn_inspect

        if "mc" in profile.special_controls and profile.path:
            btn_mc = Gtk.Button(label=self.strings["open_mc"])
            btn_mc.get_style_context().add_class("service-button")
            btn_mc.set_tooltip_text(self.strings["tooltip_mc"])
            btn_mc.connect("clicked", self.on_open_mc, st)
            btn_box.add(btn_mc)
            setattr(self, f"btn_mc_{st.value}", btn_mc)

        if "extensions" in profile.special_controls:
            btn_exts = Gtk.Button(label=self.strings["install_extensions"])
            btn_exts.get_style_context().add_class("service-button")
            btn_exts.set_tooltip_text(self.strings["tooltip_extensions"])
            btn_exts.connect("clicked", self.on_install_extensions, st)
            btn_box.add(btn_exts)
            setattr(self, f"btn_exts_{st.value}", btn_exts)

        if st == ServiceType.OLLAMA:
            btn_dockge = Gtk.Button(label=self.strings["open_dockge"])
            btn_dockge.get_style_context().add_class("service-button")
            btn_dockge.set_tooltip_text(self.strings["tooltip_open_dockge"])
            btn_dockge.connect("clicked", lambda x: webbrowser.open("http://localhost:5001"))
            btn_box.add(btn_dockge)
            self.btn_dockge = btn_dockge

        box.pack_start(btn_box, False, False, 0)

        setattr(self, f"status_label_{st.value}", status_label)

        return box

    def create_docker_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        title = Gtk.Label()
        title.get_style_context().add_class("service-title")
        title.set_text(self.strings["service_docker"])
        box.pack_start(title, False, False, 0)

        btn_install = Gtk.Button(label=self.strings["install_docker"])
        btn_install.get_style_context().add_class("service-button")
        btn_install.set_tooltip_text(self.strings["tooltip_install_docker"])
        btn_install.connect("clicked", self.on_install_docker)
        box.pack_start(btn_install, False, False, 0)
        self.btn_docker_install = btn_install

        btn_spin = Gtk.Button(label=self.strings["spin_dockge"])
        btn_spin.get_style_context().add_class("service-button")
        btn_spin.set_tooltip_text(self.strings["tooltip_spin_dockge"])
        btn_spin.connect("clicked", self.on_spin_dockge)
        box.pack_start(btn_spin, False, False, 0)
        self.btn_docker_spin = btn_spin

        return box

    def on_install_clicked(self, btn, st):
        profile = SERVICE_REGISTRY[st]
        if profile.install_cmd:
            execute_command(profile.install_cmd, f"Installing {profile.key}", parent_gui=self)

    def on_toggle_enable(self, btn, st):
        profile = SERVICE_REGISTRY[st]
        if not profile.unit_name:
            return
        is_enabled = check_systemd_unit_enabled(profile.unit_name)
        if is_enabled:
            execute_command(f"sudo systemctl disable --now {profile.unit_name}", f"Disable {profile.key}", parent_gui=self)
        else:
            execute_command(f"sudo systemctl enable --now {profile.unit_name}", f"Enable {profile.key}", parent_gui=self)
        self.refresh_service_state(st)

    def on_toggle_start_stop(self, btn, st):
        profile = SERVICE_REGISTRY[st]
        if not profile.unit_name:
            return
        if st == ServiceType.KOHYA:
            if check_systemd_unit_active(profile.unit_name):
                execute_command(f"sudo systemctl stop {KOHYA_UNIT}; sudo -u {KOHYA_USER} byobu kill-session -t {KOHYA_SESSION}", "Stop Kohya", parent_gui=self)
            else:
                env_var = 'export CUDA_VISIBLE_DEVICES="0"'
                cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
                execute_command(f"sudo -u {KOHYA_USER} -H bash -c '{cmd}'", "Start Kohya (GPU)", parent_gui=self)
        else:
            is_active = check_systemd_unit_active(profile.unit_name)
            if is_active:
                execute_command(f"sudo systemctl stop {profile.unit_name}", f"Stop {profile.key}", parent_gui=self)
            else:
                execute_command(f"sudo systemctl start {profile.unit_name}", f"Start {profile.key}", parent_gui=self)
        self.refresh_service_state(st)

    def on_restart(self, btn, st):
        profile = SERVICE_REGISTRY[st]
        if profile.unit_name:
            if st == ServiceType.KOHYA:
                env_var = 'export CUDA_VISIBLE_DEVICES="0"'
                cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
                execute_command(f"sudo systemctl stop {KOHYA_UNIT}; sudo -u {KOHYA_USER} byobu kill-session -t {KOHYA_SESSION}; sleep 2; sudo -u {KOHYA_USER} -H bash -c '{cmd}'", "Restart Kohya", parent_gui=self)
            else:
                execute_command(f"sudo systemctl restart {profile.unit_name}", f"Restart {profile.key}", parent_gui=self)
            self.refresh_service_state(st)

    def on_start_kohya_gpu(self, btn):
        env_var = 'export CUDA_VISIBLE_DEVICES="0"'
        cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
        execute_command(f"sudo -u {KOHYA_USER} -H bash -c '{cmd}'", "Start Kohya GPU", parent_gui=self)
        self.refresh_service_state(ServiceType.KOHYA)

    def on_start_kohya_cpu(self, btn):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=self.strings["cpu_warning_title"]
        )
        dialog.format_secondary_text(self.strings["cpu_warning_text"])
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            env_var = 'export CUDA_VISIBLE_DEVICES=""'
            cmd = f"{env_var} && /usr/bin/byobu new-session -d -s {KOHYA_SESSION} '{KOHYA_DIR}/gui.sh --listen 0.0.0.0 --server_port 7861 --headless'"
            execute_command(f"sudo -u {KOHYA_USER} -H bash -c '{cmd}'", "Start Kohya CPU", parent_gui=self)
            self.refresh_service_state(ServiceType.KOHYA)

    def on_inspect_kohya(self, btn):
        execute_command(f"echo 'Attaching to Kohya session...'; sleep 3; sudo -u {KOHYA_USER} byobu attach -t {KOHYA_SESSION}", "Inspect Kohya", parent_gui=self)

    def on_open_mc(self, btn, st):
        profile = SERVICE_REGISTRY[st]
        if not profile.path:
            return
        downloads = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) or os.path.expanduser("~/Downloads")
        execute_command(f"mc {downloads} {profile.path}", f"MC: {profile.key}", parent_gui=self)

    def on_install_extensions(self, btn, st):
        if st == ServiceType.FORGE:
            execute_command(_forge_extensions_install_command(), "Install Forge Extensions", parent_gui=self)

    def on_install_docker(self, btn):
        execute_command("sudo pacman -S --needed docker docker-compose && sudo systemctl enable --now docker", "Install Docker", parent_gui=self)

    def on_spin_dockge(self, btn):
        execute_command("sudo docker compose -f /docker/dockge/docker-compose.yml up -d && sleep 30 && xdg-open http://localhost:5001", "Start Dockge", parent_gui=self)

    def refresh_service_state(self, st):
        profile = SERVICE_REGISTRY[st]
        status_label = getattr(self, f"status_label_{st.value}")

        installed = False
        if profile.path:
            if profile.requires_setup_done:
                installed = check_setup_done(profile.path)
            else:
                installed = os.path.isdir(profile.path)
        else:
            installed = False

        status_parts = []
        if not installed:
            status_parts.append(self.strings["not_installed"])
        else:
            if profile.unit_name:
                active = check_systemd_unit_active(profile.unit_name)
                enabled = check_systemd_unit_enabled(profile.unit_name)
                status_parts.append(self.strings["status_active"] if active else self.strings["status_inactive"])
                status_parts.append(self.strings["status_enabled"] if enabled else self.strings["status_disabled"])
            else:
                status_parts.append("Installed")
        GLib.idle_add(status_label.set_label, " | ".join(status_parts))

        if hasattr(self, f"btn_enable_{st.value}"):
            btn_enable = getattr(self, f"btn_enable_{st.value}")
            if profile.unit_name:
                enabled = check_systemd_unit_enabled(profile.unit_name)
                GLib.idle_add(btn_enable.set_label, self.strings["disable"] if enabled else self.strings["enable"])
                GLib.idle_add(btn_enable.set_tooltip_text, self.strings["tooltip_enable"])
        if hasattr(self, f"btn_start_{st.value}"):
            btn_start = getattr(self, f"btn_start_{st.value}")
            if profile.unit_name:
                active = check_systemd_unit_active(profile.unit_name)
                GLib.idle_add(btn_start.set_label, self.strings["stop"] if active else self.strings["start"])
                GLib.idle_add(btn_start.set_tooltip_text, self.strings["tooltip_start"])
        if hasattr(self, f"btn_restart_{st.value}"):
            btn_restart = getattr(self, f"btn_restart_{st.value}")
            GLib.idle_add(btn_restart.set_tooltip_text, self.strings["tooltip_restart"])
        if hasattr(self, f"btn_install_{st.value}"):
            btn_install = getattr(self, f"btn_install_{st.value}")
            GLib.idle_add(btn_install.set_tooltip_text, self.strings["tooltip_install"])
        if hasattr(self, f"btn_mc_{st.value}"):
            btn_mc = getattr(self, f"btn_mc_{st.value}")
            GLib.idle_add(btn_mc.set_tooltip_text, self.strings["tooltip_mc"])
        if hasattr(self, f"btn_exts_{st.value}"):
            btn_exts = getattr(self, f"btn_exts_{st.value}")
            GLib.idle_add(btn_exts.set_tooltip_text, self.strings["tooltip_extensions"])
        if st == ServiceType.KOHYA:
            GLib.idle_add(self.btn_kohya_gpu.set_tooltip_text, self.strings["tooltip_kohya_gpu"])
            GLib.idle_add(self.btn_kohya_cpu.set_tooltip_text, self.strings["tooltip_kohya_cpu"])
            GLib.idle_add(self.btn_kohya_inspect.set_tooltip_text, self.strings["tooltip_inspect"])
        if st == ServiceType.OLLAMA and hasattr(self, 'btn_dockge'):
            GLib.idle_add(self.btn_dockge.set_tooltip_text, self.strings["tooltip_open_dockge"])

    def refresh_all(self):
        for st in [ServiceType.KOHYA, ServiceType.FORGE, ServiceType.COMFY, ServiceType.OLLAMA]:
            self.refresh_service_state(st)
        if hasattr(self, 'btn_docker_install'):
            GLib.idle_add(self.btn_docker_install.set_tooltip_text, self.strings["tooltip_install_docker"])
        if hasattr(self, 'btn_docker_spin'):
            GLib.idle_add(self.btn_docker_spin.set_tooltip_text, self.strings["tooltip_spin_dockge"])

    def poll_services_loop(self):
        while self.polling:
            for st in [ServiceType.KOHYA, ServiceType.FORGE, ServiceType.COMFY, ServiceType.OLLAMA]:
                self.refresh_service_state(st)
            time.sleep(5)
