"""GUI entry point for awesome-welcome."""
from awesome_welcome import config


def run_gui(services_mode=False):
    """Launch the GTK3 GUI for AwesomeWelcome and AI Services Manager."""
    config.UI_MODE = "gui"

    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    from awesome_welcome.gui.welcome import AwesomeWelcome

    win = AwesomeWelcome(services_mode=services_mode)
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()
