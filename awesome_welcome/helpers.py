"""Helper functions for command execution and environment detection."""
import os
import subprocess

from awesome_welcome import config
from awesome_welcome.i18n import STRINGS


def run_command(cmd, check=False, capture=True):
    try:
        result = subprocess.run(cmd, check=check, capture_output=capture, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def check_systemd_unit_active(unit):
    code, out, _ = run_command(["systemctl", "is-active", unit])
    return code == 0


def check_systemd_unit_enabled(unit):
    code, out, _ = run_command(["systemctl", "is-enabled", unit])
    return code == 0


def check_setup_done(path):
    return os.path.isfile(os.path.join(path, ".setup_done"))


def has_gui():
    return bool(os.environ.get("DISPLAY")) or bool(os.environ.get("WAYLAND_DISPLAY"))


def is_ssh_session():
    return bool(os.environ.get("SSH_TTY") or os.environ.get("SSH_CLIENT"))


def get_downloads_dir():
    return os.path.expanduser("~/Downloads")


def execute_command(cmd_string, title="Command", parent_gui=None, tui_app=None):
    """
    Execute command based on environment (GUI/TTY/SSH) and DRY_RUN flag.
    - GUI (DISPLAY present and not SSH): launches tilix with command.
    - TTY/SSH: runs command directly in current terminal.
    - Dry Run: displays command in a dialog (GTK or TUI modal).
    """
    if config.DRY_RUN:
        if config.UI_MODE == "gui":
            if parent_gui:
                import gi
                gi.require_version("Gtk", "3.0")
                from gi.repository import Gtk, GLib
                dialog = Gtk.MessageDialog(
                    transient_for=parent_gui,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text=STRINGS[parent_gui.lang]["dry_run_title"]
                )
                dialog.format_secondary_text(STRINGS[parent_gui.lang]["dry_run_text"].format(command=cmd_string))
                dialog.run()
                dialog.destroy()
        elif config.UI_MODE == "tui":
            if tui_app:
                from awesome_welcome.tui.dialogs import DryRunModal
                tui_app.push_screen(DryRunModal(cmd_string, tui_app.lang.current))
        return

    # Real execution
    if has_gui() and not is_ssh_session():
        cmd = f'tilix -t "{title}" -e "bash -c \'{cmd_string}; echo; echo Press Enter to close; read\'"'
        subprocess.Popen(cmd, shell=True)
    else:
        shell_cmd = f'bash -c "{cmd_string}; echo; echo Press Enter to close; read"'
        if tui_app is not None:
            with tui_app.suspend():
                subprocess.run(shell_cmd, shell=True)
        else:
            subprocess.run(shell_cmd, shell=True)
