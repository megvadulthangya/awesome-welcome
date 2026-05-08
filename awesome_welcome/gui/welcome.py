"""GTK3 Welcome window."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import os
import subprocess
import webbrowser

from awesome_welcome.config import (
    APP_TITLE, AUTOSTART_DIR, AUTOSTART_FILE, SOURCE_DESKTOP_FILE,
    LINKS_PROJECT, LINKS_MANJARO
)
from awesome_welcome.i18n import STRINGS
from awesome_welcome.gui.css import CSS_DATA
from awesome_welcome.gui.manager import AIServicesManagerGTK


class AwesomeWelcome(Gtk.Window):
    def __init__(self, services_mode=False):
        super().__init__(title=APP_TITLE)
        self.services_mode = services_mode
        self.is_live = os.path.exists("/run/miso/bootmnt/manjaro")

        self.set_border_width(20)
        self.set_default_size(700, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_DATA.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = APP_TITLE
        self.set_titlebar(header)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        lbl_title = Gtk.Label(label=STRINGS["en"]["welcome_title"])
        lbl_title.get_style_context().add_class("title-label")
        vbox.pack_start(lbl_title, False, False, 0)

        lbl_desc = Gtk.Label(label=STRINGS["en"]["welcome_desc"])
        lbl_desc.get_style_context().add_class("desc-label")
        vbox.pack_start(lbl_desc, False, False, 0)

        main_actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.pack_start(main_actions_box, False, False, 10)

        if self.is_live:
            btn_install = Gtk.Button(label=STRINGS["en"]["install_manjaro"])
            btn_install.get_style_context().add_class("action-btn")
            btn_install.connect("clicked", self.on_install_manjaro)
            try:
                icon = Gtk.Image.new_from_icon_name("system-os-installer", Gtk.IconSize.BUTTON)
                btn_install.set_image(icon)
                btn_install.set_always_show_image(True)
            except Exception:
                pass
            main_actions_box.pack_start(btn_install, False, False, 0)
            lbl_live = Gtk.Label(label=STRINGS["en"]["live_env"])
            main_actions_box.pack_start(lbl_live, False, False, 0)
        else:
            grid = Gtk.Grid()
            grid.set_column_spacing(10)
            grid.set_row_spacing(10)
            grid.set_halign(Gtk.Align.CENTER)

            self.btn_services = Gtk.Button(label=STRINGS["en"]["manage_services"])
            self.btn_services.get_style_context().add_class("action-btn")
            self.btn_services.set_size_request(250, 50)
            self.btn_services.set_tooltip_text(STRINGS["en"]["manage_services_tooltip"])
            self.btn_services.connect("clicked", self.on_manage_services)
            try:
                icon = Gtk.Image.new_from_icon_name("system-run", Gtk.IconSize.BUTTON)
                self.btn_services.set_image(icon)
                self.btn_services.set_always_show_image(True)
            except Exception:
                pass
            grid.attach(self.btn_services, 0, 0, 1, 1)

            btn_pamac = Gtk.Button(label=STRINGS["en"]["manage_software"])
            btn_pamac.get_style_context().add_class("action-btn")
            btn_pamac.set_size_request(250, 50)
            btn_pamac.set_tooltip_text("Open Pamac Software Manager")
            try:
                icon_pamac = Gtk.Image.new_from_icon_name("system-software-install", Gtk.IconSize.BUTTON)
                btn_pamac.set_image(icon_pamac)
                btn_pamac.set_always_show_image(True)
            except Exception:
                pass
            btn_pamac.connect("clicked", self.on_open_pamac)
            grid.attach(btn_pamac, 1, 0, 1, 1)

            btn_wall = Gtk.Button(label=STRINGS["en"]["install_wallpapers"])
            btn_wall.get_style_context().add_class("action-btn")
            btn_wall.set_size_request(510, 50)
            btn_wall.set_tooltip_text("Installs 'nordic-backgrounds' package")
            try:
                icon_wall = Gtk.Image.new_from_icon_name("preferences-desktop-wallpaper", Gtk.IconSize.BUTTON)
                btn_wall.set_image(icon_wall)
                btn_wall.set_always_show_image(True)
            except Exception:
                pass
            btn_wall.connect("clicked", self.on_install_wallpapers)
            grid.attach(btn_wall, 0, 1, 2, 1)

            main_actions_box.pack_start(grid, False, False, 0)

        lbl_proj = Gtk.Label(label=STRINGS["en"]["project_support"])
        lbl_proj.get_style_context().add_class("section-label")
        vbox.pack_start(lbl_proj, False, False, 5)
        box_proj = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_proj.set_halign(Gtk.Align.CENTER)
        for name, url in LINKS_PROJECT.items():
            self.add_link_button(box_proj, name, url)
        vbox.pack_start(box_proj, False, False, 0)

        lbl_manjaro = Gtk.Label(label=STRINGS["en"]["manjaro_official"])
        lbl_manjaro.get_style_context().add_class("section-label")
        vbox.pack_start(lbl_manjaro, False, False, 5)
        box_manjaro = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_manjaro.set_halign(Gtk.Align.CENTER)
        for name, url in LINKS_MANJARO.items():
            self.add_link_button(box_manjaro, name, url)
        vbox.pack_start(box_manjaro, False, False, 0)

        if not self.is_live:
            autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            autostart_box.set_halign(Gtk.Align.CENTER)
            autostart_box.get_style_context().add_class("autostart-box")
            lbl_autostart = Gtk.Label(label=STRINGS["en"]["launch_at_start"])
            self.switch_autostart = Gtk.Switch()
            self.switch_autostart.set_active(os.path.lexists(AUTOSTART_FILE))
            self.switch_autostart.connect("notify::active", self.on_autostart_toggled)
            autostart_box.pack_start(lbl_autostart, False, False, 0)
            autostart_box.pack_start(self.switch_autostart, False, False, 0)
            vbox.pack_end(autostart_box, False, False, 10)

        self.show_all()

        if self.services_mode and not self.is_live:
            GLib.idle_add(self.on_manage_services, None)

    def add_link_button(self, box, label, url):
        btn = Gtk.Button(label=label)
        btn.get_style_context().add_class("link-btn")
        btn.connect("clicked", lambda x: webbrowser.open(url))
        box.pack_start(btn, False, False, 0)

    def on_open_pamac(self, widget):
        try:
            subprocess.Popen(["pamac-manager"])
        except Exception as e:
            self.show_error(f"Error opening software manager: {e}")

    def on_install_wallpapers(self, widget):
        try:
            cmd = "pamac install nordic-backgrounds; echo; echo 'Done. Press Enter to close.'; read"
            subprocess.Popen(["tilix", "-e", "sh", "-c", cmd])
        except Exception as e:
            self.show_error(f"Failed to open terminal: {e}")

    def on_autostart_toggled(self, switch, gparam):
        if switch.get_active():
            try:
                if not os.path.exists(AUTOSTART_DIR):
                    os.makedirs(AUTOSTART_DIR)
                if os.path.lexists(AUTOSTART_FILE):
                    os.remove(AUTOSTART_FILE)
                os.symlink(SOURCE_DESKTOP_FILE, AUTOSTART_FILE)
            except Exception as e:
                print(f"Error enabling autostart: {e}")
                switch.set_active(False)
        else:
            try:
                if os.path.lexists(AUTOSTART_FILE):
                    os.remove(AUTOSTART_FILE)
            except Exception as e:
                print(f"Error disabling autostart: {e}")

    def on_install_manjaro(self, widget):
        try:
            subprocess.Popen(["calamares_polkit"])
            self.close()
        except Exception as e:
            self.show_error(f"Failed to launch installer: {e}")

    def on_manage_services(self, widget):
        self.hide()
        manager = AIServicesManagerGTK(parent_welcome=self)
        manager.show_all()

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=STRINGS["en"]["error"]
        )
        dialog.format_secondary_text(str(message))
        dialog.run()
        dialog.destroy()
