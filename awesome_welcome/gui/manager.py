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
from awesome_welcome.services.ollama import (
    detect_ollama_installed, ollama_update_command, ollama_uninstall_command,
    get_webui_url, set_webui_url
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
        dockge_page = self.notebook.get_nth_page(5)
        if dockge_page:
            label = self.notebook.get_tab_label(dockge_page)
            label.set_text(self.strings["service_dockge"])
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

        dockge_page = self.create_dockge_page()
        label = Gtk.Label(label=self.strings["service_dockge"])
        self.notebook.append_page(dockge_page, label)

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

            installed_label = Gtk.Label()
            installed_label.set_xalign(0)
            installed_label.set_margin_top(2)
            installed_label.set_margin_bottom(2)
            box.pack_start(installed_label, False, False, 0)
            self.forge_installed_label = installed_label
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
            tooltip_key = "tooltip_install_ollama" if st == ServiceType.OLLAMA else "tooltip_install_venv"
            btn_install = Gtk.Button(label=self.strings["install"])
            btn_install.get_style_context().add_class("service-button")
            btn_install.set_tooltip_text(self.strings[tooltip_key])
            if st == ServiceType.OLLAMA:
                btn_install.connect("clicked", self.on_install_clicked_ollama_aware, st)
            else:
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

            btn_thunar = Gtk.Button(label=self.strings["open_thunar"])
            btn_thunar.get_style_context().add_class("service-button")
            btn_thunar.set_tooltip_text(self.strings["tooltip_thunar"])
            btn_thunar.connect("clicked", self.on_open_thunar, st)
            btn_box.add(btn_thunar)
            setattr(self, f"btn_thunar_{st.value}", btn_thunar)

        if "extensions" in profile.special_controls:
            btn_exts = Gtk.Button(label=self.strings["install_extensions"])
            btn_exts.get_style_context().add_class("service-button")
            btn_exts.set_tooltip_text(self.strings["tooltip_extensions"])
            btn_exts.connect("clicked", self.on_install_extensions, st)
            btn_box.add(btn_exts)
            setattr(self, f"btn_exts_{st.value}", btn_exts)

        if st == ServiceType.FORGE:
            btn_pip_refresh = Gtk.Button(label=self.strings["forge_pip_refresh"])
            btn_pip_refresh.get_style_context().add_class("service-button")
            btn_pip_refresh.set_tooltip_text(self.strings["tooltip_forge_pip_refresh"])
            btn_pip_refresh.connect("clicked", self.on_forge_pip_refresh)
            btn_box.add(btn_pip_refresh)
            self.btn_forge_pip_refresh = btn_pip_refresh

            btn_venv_rebuild = Gtk.Button(label=self.strings["forge_venv_rebuild"])
            btn_venv_rebuild.get_style_context().add_class("service-button")
            btn_venv_rebuild.set_tooltip_text(self.strings["tooltip_forge_venv_rebuild"])
            btn_venv_rebuild.connect("clicked", self.on_forge_venv_rebuild)
            btn_box.add(btn_venv_rebuild)
            self.btn_forge_venv_rebuild = btn_venv_rebuild

            btn_switch = Gtk.Button(label=self.strings["forge_switch_version"])
            btn_switch.get_style_context().add_class("service-button")
            btn_switch.set_tooltip_text(self.strings["tooltip_forge_switch_version"])
            btn_switch.connect("clicked", self.on_forge_switch_version)
            btn_box.add(btn_switch)
            self.btn_forge_switch = btn_switch

            btn_purge = Gtk.Button(label=self.strings["forge_purge"])
            btn_purge.get_style_context().add_class("service-button")
            btn_purge.set_tooltip_text(self.strings["tooltip_forge_purge"])
            btn_purge.connect("clicked", self.on_forge_purge)
            btn_box.add(btn_purge)
            self.btn_forge_purge = btn_purge

        if st == ServiceType.OLLAMA:
            btn_webui = Gtk.Button(label=self.strings["open_webui"])
            btn_webui.get_style_context().add_class("service-button")
            btn_webui.set_tooltip_text(self.strings["tooltip_open_webui"])
            btn_webui.connect("clicked", self.on_open_webui)
            btn_box.add(btn_webui)
            self.btn_ollama_webui = btn_webui

            btn_edit_url = Gtk.Button(label=self.strings["edit_webui_url"])
            btn_edit_url.get_style_context().add_class("service-button")
            btn_edit_url.set_tooltip_text(self.strings["tooltip_edit_webui_url"])
            btn_edit_url.connect("clicked", self.on_edit_webui_url)
            btn_box.add(btn_edit_url)
            self.btn_ollama_edit_url = btn_edit_url

            btn_remove = Gtk.Button(label=self.strings["remove_ollama"])
            btn_remove.get_style_context().add_class("service-button")
            btn_remove.set_tooltip_text(self.strings["tooltip_remove_ollama"])
            btn_remove.connect("clicked", self.on_remove_ollama)
            btn_box.add(btn_remove)
            self.btn_ollama_remove = btn_remove

        box.pack_start(btn_box, False, False, 0)

        setattr(self, f"status_label_{st.value}", status_label)

        return box

    def create_docker_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        hbox_title = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title = Gtk.Label()
        title.get_style_context().add_class("service-title")
        title.set_text(self.strings["service_docker"])
        hbox_title.pack_start(title, False, False, 0)

        status = Gtk.Label()
        status.get_style_context().add_class("service-status")
        hbox_title.pack_end(status, False, False, 0)
        box.pack_start(hbox_title, False, False, 0)
        self.docker_status_label = status

        btn_box = Gtk.FlowBox()
        btn_box.set_selection_mode(Gtk.SelectionMode.NONE)
        btn_box.set_homogeneous(False)
        btn_box.set_column_spacing(5)
        btn_box.set_row_spacing(5)

        btn_install = Gtk.Button(label=self.strings["install_docker"])
        btn_install.get_style_context().add_class("service-button")
        btn_install.set_tooltip_text(self.strings["tooltip_install_docker"])
        btn_install.connect("clicked", self.on_install_docker)
        btn_box.add(btn_install)
        self.btn_docker_install = btn_install

        btn_start = Gtk.Button(label=self.strings["start_docker"])
        btn_start.get_style_context().add_class("service-button")
        btn_start.set_tooltip_text(self.strings["tooltip_start_docker"])
        btn_start.connect("clicked", self.on_docker_start_stop)
        btn_box.add(btn_start)
        self.btn_docker_start = btn_start

        btn_restart = Gtk.Button(label=self.strings["restart_docker"])
        btn_restart.get_style_context().add_class("service-button")
        btn_restart.set_tooltip_text(self.strings["tooltip_restart_docker"])
        btn_restart.connect("clicked", self.on_docker_restart)
        btn_box.add(btn_restart)
        self.btn_docker_restart = btn_restart

        btn_clean1 = Gtk.Button(label=self.strings["cleanup_docker_basic"])
        btn_clean1.get_style_context().add_class("service-button")
        btn_clean1.set_tooltip_text(self.strings["tooltip_cleanup_docker_basic"])
        btn_clean1.connect("clicked", self.on_docker_cleanup_basic)
        btn_box.add(btn_clean1)
        self.btn_docker_clean_basic = btn_clean1

        btn_clean2 = Gtk.Button(label=self.strings["cleanup_docker_images"])
        btn_clean2.get_style_context().add_class("service-button")
        btn_clean2.set_tooltip_text(self.strings["tooltip_cleanup_docker_images"])
        btn_clean2.connect("clicked", self.on_docker_cleanup_images)
        btn_box.add(btn_clean2)
        self.btn_docker_clean_images = btn_clean2

        btn_clean3 = Gtk.Button(label=self.strings["cleanup_docker_volumes"])
        btn_clean3.get_style_context().add_class("service-button")
        btn_clean3.set_tooltip_text(self.strings["tooltip_cleanup_docker_volumes"])
        btn_clean3.connect("clicked", self.on_docker_cleanup_volumes)
        btn_box.add(btn_clean3)
        self.btn_docker_clean_volumes = btn_clean3

        box.pack_start(btn_box, False, False, 0)
        return box

    def create_dockge_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        hbox_title = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title = Gtk.Label()
        title.get_style_context().add_class("service-title")
        title.set_text(self.strings["service_dockge"])
        hbox_title.pack_start(title, False, False, 0)

        status = Gtk.Label()
        status.get_style_context().add_class("service-status")
        hbox_title.pack_end(status, False, False, 0)
        box.pack_start(hbox_title, False, False, 0)
        self.dockge_status_label = status

        btn_box = Gtk.FlowBox()
        btn_box.set_selection_mode(Gtk.SelectionMode.NONE)
        btn_box.set_homogeneous(False)
        btn_box.set_column_spacing(5)
        btn_box.set_row_spacing(5)

        btn_spin = Gtk.Button(label=self.strings["spin_dockge"])
        btn_spin.get_style_context().add_class("service-button")
        btn_spin.set_tooltip_text(self.strings["tooltip_spin_dockge"])
        btn_spin.connect("clicked", self.on_dockge_spin_stop)
        btn_box.add(btn_spin)
        self.btn_dockge_spin = btn_spin

        btn_open = Gtk.Button(label=self.strings["open_dockge"])
        btn_open.get_style_context().add_class("service-button")
        btn_open.set_tooltip_text(self.strings["tooltip_open_dockge"])
        btn_open.connect("clicked", self.on_dockge_open)
        btn_box.add(btn_open)
        self.btn_dockge_open = btn_open

        btn_restart = Gtk.Button(label=self.strings["restart_dockge"])
        btn_restart.get_style_context().add_class("service-button")
        btn_restart.set_tooltip_text(self.strings["tooltip_restart_dockge"])
        btn_restart.connect("clicked", self.on_dockge_restart)
        btn_box.add(btn_restart)
        self.btn_dockge_restart = btn_restart

        box.pack_start(btn_box, False, False, 0)
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

    def on_open_thunar(self, btn, st):
        profile = SERVICE_REGISTRY[st]
        if not profile.path:
            return
        execute_command(f"thunar {profile.path}", f"Thunar: {profile.key}", parent_gui=self)

    def on_install_extensions(self, btn, st):
        if st != ServiceType.FORGE:
            return
        from awesome_welcome.services.forge import FORGE_EXTENSIONS, _forge_extensions_install_command

        dialog = Gtk.Dialog(
            title=self.strings["ext_dialog_title"],
            transient_for=self,
            flags=0,
        )
        dialog.set_default_size(1000, 800)

        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_top(10)
        content.set_margin_start(10)
        content.set_margin_end(10)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(640)

        listbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        checks = []
        for ext in FORGE_EXTENSIONS:
            cb = Gtk.CheckButton(label=ext["name"])
            cb.set_active(True)
            checks.append((cb, ext))
            listbox.pack_start(cb, False, False, 0)

        scrolled.add(listbox)
        content.pack_start(scrolled, True, True, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.CENTER)

        btn_all = Gtk.Button(label=self.strings["ext_select_all"])
        btn_all.connect("clicked", lambda w: [cb.set_active(True) for cb, _ in checks])
        btn_box.pack_start(btn_all, False, False, 0)

        btn_none = Gtk.Button(label=self.strings["ext_deselect_all"])
        btn_none.connect("clicked", lambda w: [cb.set_active(False) for cb, _ in checks])
        btn_box.pack_start(btn_none, False, False, 0)

        content.pack_start(btn_box, False, False, 0)

        dialog.add_button(self.strings["ext_cancel"], Gtk.ResponseType.CANCEL)
        dialog.add_button(self.strings["ext_install_selected"], Gtk.ResponseType.OK)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            selected = [ext for cb, ext in checks if cb.get_active()]
            if selected:
                execute_command(_forge_extensions_install_command(selected), "Install Forge Extensions", parent_gui=self)

        dialog.destroy()

    def on_forge_pip_refresh(self, btn):
        from awesome_welcome.services.forge import detect_forge_flavor, forge_pip_refresh_command
        flavor = detect_forge_flavor()
        if not flavor:
            self._show_error("Cannot detect installed Forge flavor.")
            return
        execute_command(forge_pip_refresh_command(flavor), "Forge: Pip Refresh", parent_gui=self)

    def on_forge_venv_rebuild(self, btn):
        from awesome_welcome.services.forge import detect_forge_flavor, forge_rebuild_venv_command
        flavor = detect_forge_flavor()
        if not flavor:
            self._show_error("Cannot detect installed Forge flavor.")
            return
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=self.strings["forge_confirm_rebuild"]
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            execute_command(forge_rebuild_venv_command(flavor), "Forge: Rebuild venv", parent_gui=self)

    def on_forge_switch_version(self, btn):
        from awesome_welcome.services.forge import detect_forge_package, forge_purge_command, forge_install_package_command
        current_pkg = detect_forge_package()

        dialog = Gtk.Dialog(
            title=self.strings["forge_switch_version"],
            transient_for=self, flags=0,
        )
        dialog.set_default_size(520, 320)
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_top(10)
        content.set_margin_start(10)
        content.set_margin_end(10)

        if current_pkg:
            installed = Gtk.Label()
            installed.set_xalign(0)
            installed.set_markup(
                "<b>" + self.strings["forge_installed_label"].format(pkg=current_pkg) + "</b>"
            )
            content.pack_start(installed, False, False, 0)
        else:
            installed = Gtk.Label(label=self.strings["forge_not_installed_label"])
            installed.set_xalign(0)
            content.pack_start(installed, False, False, 0)

        warn = Gtk.Label(label=self.strings["forge_purge_warning"])
        warn.set_line_wrap(True)
        warn.get_style_context().add_class("warning-label")
        content.pack_start(warn, False, False, 0)

        versions = [
            ("stable-diffusion-webui-forge", self.strings["forge_version_forge"]),
            ("stable-diffusion-webui-forge-cu124", self.strings["forge_version_cu124"]),
            ("stable-diffusion-webui-forge-neo-git", self.strings["forge_version_neo"]),
        ]
        radios = []
        first = None
        for pkg, label_text in versions:
            if first is None:
                rb = Gtk.RadioButton.new_with_label(None, label_text)
                first = rb
            else:
                rb = Gtk.RadioButton.new_with_label_from_widget(first, label_text)
            rb.pkg_name = pkg
            radios.append(rb)
            content.pack_start(rb, False, False, 0)

        if current_pkg:
            for rb in radios:
                if rb.pkg_name == current_pkg:
                    rb.set_active(True)
                    break

        dialog.add_button(self.strings.get("ext_cancel", "Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button("OK", Gtk.ResponseType.OK)
        dialog.show_all()
        response = dialog.run()

        selected_pkg = None
        if response == Gtk.ResponseType.OK:
            for rb in radios:
                if rb.get_active():
                    selected_pkg = rb.pkg_name
                    break
        dialog.destroy()

        if not selected_pkg:
            return

        if current_pkg and selected_pkg == current_pkg:
            self._show_info(self.strings["forge_switch_no_change"])
            return

        confirm = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=self.strings["forge_switch_confirm_title"],
        )
        confirm.format_secondary_text(
            self.strings["forge_switch_confirm_text"].format(
                current=current_pkg or "-", target=selected_pkg
            )
        )
        confirm_resp = confirm.run()
        confirm.destroy()
        if confirm_resp != Gtk.ResponseType.OK:
            return

        cmd_parts = []
        if current_pkg:
            cmd_parts.append(forge_purge_command(current_pkg))
        cmd_parts.append(forge_install_package_command(selected_pkg))
        execute_command(" && ".join(cmd_parts), "Forge: Switch Version", parent_gui=self)
        self.refresh_service_state(ServiceType.FORGE)

    def on_forge_purge(self, btn):
        from awesome_welcome.services.forge import detect_forge_package, forge_purge_command, FORGE_INSTALL_DIR
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=self.strings["forge_purge_warning"]
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            pkg = detect_forge_package()
            if pkg:
                execute_command(forge_purge_command(pkg), "Forge: Purge", parent_gui=self)
            else:
                execute_command(f"sudo rm -rf {FORGE_INSTALL_DIR}", "Forge: Remove files", parent_gui=self)
        self.refresh_service_state(ServiceType.FORGE)

    def _show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=self.strings.get("error", "Error")
        )
        dialog.format_secondary_text(str(message))
        dialog.run()
        dialog.destroy()

    def _show_info(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=str(message),
        )
        dialog.run()
        dialog.destroy()

    def on_install_docker(self, btn):
        if detect_docker_installed():
            execute_command(docker_reinstall_command(), "Reinstall Docker", parent_gui=self)
        else:
            execute_command(docker_install_command(), "Install Docker", parent_gui=self)
        self._refresh_docker_state()

    def on_docker_start_stop(self, btn):
        if not detect_docker_installed():
            return
        if check_systemd_unit_active("docker.service"):
            execute_command(docker_stop_command(), "Stop Docker", parent_gui=self)
        else:
            execute_command(docker_start_command(), "Start Docker", parent_gui=self)
        self._refresh_docker_state()

    def on_docker_restart(self, btn):
        if not detect_docker_installed():
            return
        execute_command(docker_restart_command(), "Restart Docker", parent_gui=self)
        self._refresh_docker_state()

    def on_docker_cleanup_basic(self, btn):
        if not detect_docker_installed():
            return
        execute_command(docker_prune_command(), "Docker cleanup", parent_gui=self)

    def on_docker_cleanup_images(self, btn):
        if not detect_docker_installed():
            return
        execute_command(docker_prune_images_command(), "Docker cleanup + images", parent_gui=self)

    def on_docker_cleanup_volumes(self, btn):
        if not detect_docker_installed():
            return
        confirm = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=self.strings["cleanup_docker_volumes_warning"],
        )
        resp = confirm.run()
        confirm.destroy()
        if resp == Gtk.ResponseType.OK:
            execute_command(docker_prune_volumes_command(), "Docker cleanup + volumes", parent_gui=self)

    def on_dockge_spin_stop(self, btn):
        if detect_dockge_running():
            execute_command(dockge_stop_command(), "Stop Dockge", parent_gui=self)
        else:
            execute_command(dockge_up_command(), "Spin up Dockge", parent_gui=self)
        self._refresh_dockge_state()

    def on_dockge_open(self, btn):
        execute_command(dockge_open_command(), "Open Dockge", parent_gui=self)

    def on_dockge_restart(self, btn):
        execute_command(dockge_restart_command(), "Restart Dockge", parent_gui=self)
        self._refresh_dockge_state()

    def on_open_webui(self, btn):
        url = get_webui_url()
        try:
            webbrowser.open(url)
        except Exception as e:
            self._show_error(str(e))

    def on_edit_webui_url(self, btn):
        dialog = Gtk.Dialog(
            title=self.strings["webui_url_dialog_title"],
            transient_for=self, flags=0,
        )
        dialog.set_default_size(420, 120)
        content = dialog.get_content_area()
        content.set_spacing(8)
        content.set_margin_top(10)
        content.set_margin_start(10)
        content.set_margin_end(10)

        prompt = Gtk.Label(label=self.strings["webui_url_dialog_prompt"])
        prompt.set_xalign(0)
        content.pack_start(prompt, False, False, 0)

        entry = Gtk.Entry()
        entry.set_text(get_webui_url())
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 0)

        dialog.add_button(self.strings["ext_cancel"], Gtk.ResponseType.CANCEL)
        ok_btn = dialog.add_button("OK", Gtk.ResponseType.OK)
        ok_btn.set_can_default(True)
        ok_btn.grab_default()
        dialog.show_all()
        resp = dialog.run()
        new_url = entry.get_text().strip()
        dialog.destroy()
        if resp == Gtk.ResponseType.OK and new_url:
            try:
                set_webui_url(new_url)
                self._show_info(self.strings["webui_url_saved"])
            except Exception as e:
                self._show_error(str(e))

    def on_install_clicked_ollama_aware(self, btn, st):
        """Wrap Install/Update for Ollama: re-runs the install script either way."""
        if st == ServiceType.OLLAMA and detect_ollama_installed():
            execute_command(ollama_update_command(), "Update Ollama", parent_gui=self)
        else:
            self.on_install_clicked(btn, st)
        self.refresh_service_state(st)

    def on_remove_ollama(self, btn):
        confirm = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=self.strings["ollama_remove_warning"],
        )
        resp = confirm.run()
        confirm.destroy()
        if resp == Gtk.ResponseType.OK:
            execute_command(ollama_uninstall_command(), "Remove Ollama", parent_gui=self)
            self.refresh_service_state(ServiceType.OLLAMA)

    def refresh_service_state(self, st):
        profile = SERVICE_REGISTRY[st]
        status_label = getattr(self, f"status_label_{st.value}")

        if st == ServiceType.OLLAMA:
            installed = detect_ollama_installed()
        elif profile.path:
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
            if st == ServiceType.OLLAMA:
                if installed:
                    GLib.idle_add(btn_install.set_label, self.strings["update_ollama"])
                    GLib.idle_add(btn_install.set_tooltip_text, self.strings["tooltip_update_ollama"])
                else:
                    GLib.idle_add(btn_install.set_label, self.strings["install"])
                    GLib.idle_add(btn_install.set_tooltip_text, self.strings["tooltip_install_ollama"])
            else:
                GLib.idle_add(btn_install.set_label, self.strings["install"])
                GLib.idle_add(btn_install.set_tooltip_text, self.strings["tooltip_install_venv"])
        if hasattr(self, f"btn_mc_{st.value}"):
            btn_mc = getattr(self, f"btn_mc_{st.value}")
            GLib.idle_add(btn_mc.set_tooltip_text, self.strings["tooltip_mc"])
        if hasattr(self, f"btn_thunar_{st.value}"):
            btn_thunar = getattr(self, f"btn_thunar_{st.value}")
            GLib.idle_add(btn_thunar.set_tooltip_text, self.strings["tooltip_thunar"])
        if hasattr(self, f"btn_exts_{st.value}"):
            btn_exts = getattr(self, f"btn_exts_{st.value}")
            GLib.idle_add(btn_exts.set_tooltip_text, self.strings["tooltip_extensions"])
        if st == ServiceType.KOHYA:
            GLib.idle_add(self.btn_kohya_gpu.set_tooltip_text, self.strings["tooltip_kohya_gpu"])
            GLib.idle_add(self.btn_kohya_cpu.set_tooltip_text, self.strings["tooltip_kohya_cpu"])
            GLib.idle_add(self.btn_kohya_inspect.set_tooltip_text, self.strings["tooltip_inspect"])
        if st == ServiceType.FORGE and hasattr(self, "forge_installed_label"):
            from awesome_welcome.services.forge import detect_forge_package
            pkg = detect_forge_package()
            if pkg:
                txt = self.strings["forge_installed_label"].format(pkg=pkg)
            else:
                txt = self.strings["forge_not_installed_label"]
            GLib.idle_add(self.forge_installed_label.set_markup, f"<b>{txt}</b>")
        if st == ServiceType.OLLAMA:
            if hasattr(self, "btn_ollama_webui"):
                GLib.idle_add(self.btn_ollama_webui.set_tooltip_text, self.strings["tooltip_open_webui"])
            if hasattr(self, "btn_ollama_edit_url"):
                GLib.idle_add(self.btn_ollama_edit_url.set_tooltip_text, self.strings["tooltip_edit_webui_url"])
                GLib.idle_add(self.btn_ollama_edit_url.set_label, self.strings["edit_webui_url"])
            if hasattr(self, "btn_ollama_remove"):
                GLib.idle_add(self.btn_ollama_remove.set_tooltip_text, self.strings["tooltip_remove_ollama"])
                GLib.idle_add(self.btn_ollama_remove.set_label, self.strings["remove_ollama"])
                GLib.idle_add(self.btn_ollama_remove.set_sensitive, installed)

    def _refresh_docker_state(self):
        if not hasattr(self, "docker_status_label"):
            return
        installed = detect_docker_installed()
        if not installed:
            status = self.strings["docker_status_not_installed"]
        elif check_systemd_unit_active("docker.service"):
            status = self.strings["docker_status_running"]
        else:
            status = self.strings["docker_status_stopped"]
        GLib.idle_add(self.docker_status_label.set_label, status)

        if hasattr(self, "btn_docker_install"):
            label_key = "reinstall_docker" if installed else "install_docker"
            tip_key = "tooltip_reinstall_docker" if installed else "tooltip_install_docker"
            GLib.idle_add(self.btn_docker_install.set_label, self.strings[label_key])
            GLib.idle_add(self.btn_docker_install.set_tooltip_text, self.strings[tip_key])

        for attr, sensitive in [
            ("btn_docker_start", installed),
            ("btn_docker_restart", installed),
            ("btn_docker_clean_basic", installed),
            ("btn_docker_clean_images", installed),
            ("btn_docker_clean_volumes", installed),
        ]:
            if hasattr(self, attr):
                GLib.idle_add(getattr(self, attr).set_sensitive, sensitive)

        if installed and hasattr(self, "btn_docker_start"):
            running = check_systemd_unit_active("docker.service")
            label_key = "stop_docker" if running else "start_docker"
            tip_key = "tooltip_stop_docker" if running else "tooltip_start_docker"
            GLib.idle_add(self.btn_docker_start.set_label, self.strings[label_key])
            GLib.idle_add(self.btn_docker_start.set_tooltip_text, self.strings[tip_key])

        if hasattr(self, "btn_docker_restart"):
            GLib.idle_add(self.btn_docker_restart.set_label, self.strings["restart_docker"])
            GLib.idle_add(self.btn_docker_restart.set_tooltip_text, self.strings["tooltip_restart_docker"])
        if hasattr(self, "btn_docker_clean_basic"):
            GLib.idle_add(self.btn_docker_clean_basic.set_label, self.strings["cleanup_docker_basic"])
            GLib.idle_add(self.btn_docker_clean_basic.set_tooltip_text, self.strings["tooltip_cleanup_docker_basic"])
        if hasattr(self, "btn_docker_clean_images"):
            GLib.idle_add(self.btn_docker_clean_images.set_label, self.strings["cleanup_docker_images"])
            GLib.idle_add(self.btn_docker_clean_images.set_tooltip_text, self.strings["tooltip_cleanup_docker_images"])
        if hasattr(self, "btn_docker_clean_volumes"):
            GLib.idle_add(self.btn_docker_clean_volumes.set_label, self.strings["cleanup_docker_volumes"])
            GLib.idle_add(self.btn_docker_clean_volumes.set_tooltip_text, self.strings["tooltip_cleanup_docker_volumes"])

    def _refresh_dockge_state(self):
        if not hasattr(self, "dockge_status_label"):
            return
        docker_installed = detect_docker_installed()
        if not docker_installed:
            status = self.strings["dockge_status_not_installed"]
            running = False
        else:
            running = detect_dockge_running()
            status = self.strings["dockge_status_running"] if running else self.strings["dockge_status_stopped"]
        GLib.idle_add(self.dockge_status_label.set_label, status)

        if hasattr(self, "btn_dockge_spin"):
            label_key = "stop_dockge" if running else "spin_dockge"
            tip_key = "tooltip_stop_dockge" if running else "tooltip_spin_dockge"
            GLib.idle_add(self.btn_dockge_spin.set_label, self.strings[label_key])
            GLib.idle_add(self.btn_dockge_spin.set_tooltip_text, self.strings[tip_key])
            GLib.idle_add(self.btn_dockge_spin.set_sensitive, docker_installed)
        if hasattr(self, "btn_dockge_open"):
            GLib.idle_add(self.btn_dockge_open.set_label, self.strings["open_dockge"])
            GLib.idle_add(self.btn_dockge_open.set_tooltip_text, self.strings["tooltip_open_dockge"])
            GLib.idle_add(self.btn_dockge_open.set_sensitive, running)
        if hasattr(self, "btn_dockge_restart"):
            GLib.idle_add(self.btn_dockge_restart.set_label, self.strings["restart_dockge"])
            GLib.idle_add(self.btn_dockge_restart.set_tooltip_text, self.strings["tooltip_restart_dockge"])
            GLib.idle_add(self.btn_dockge_restart.set_sensitive, running)

    def refresh_all(self):
        for st in [ServiceType.KOHYA, ServiceType.FORGE, ServiceType.COMFY, ServiceType.OLLAMA]:
            self.refresh_service_state(st)
        self._refresh_docker_state()
        self._refresh_dockge_state()

    def poll_services_loop(self):
        while self.polling:
            for st in [ServiceType.KOHYA, ServiceType.FORGE, ServiceType.COMFY, ServiceType.OLLAMA]:
                self.refresh_service_state(st)
            self._refresh_docker_state()
            self._refresh_dockge_state()
            time.sleep(5)
