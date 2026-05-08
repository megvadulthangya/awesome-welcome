"""TUI modal dialogs."""
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.containers import Container, Horizontal
from textual.app import ComposeResult

from awesome_welcome.i18n import STRINGS


class ConfirmDialog(ModalScreen):
    """Simple confirmation dialog for CPU mode warning."""
    def __init__(self, message):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.message, classes="dialog-message"),
            Horizontal(
                Button("Yes", variant="error", id="yes"),
                Button("No", variant="primary", id="no"),
                classes="dialog-buttons"
            ),
            classes="dialog"
        )

    def on_button_pressed(self, event):
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)


class DryRunModal(ModalScreen):
    """Modal to show dry-run command."""
    def __init__(self, command, lang):
        super().__init__()
        self.command = command
        self.lang = lang

    def compose(self) -> ComposeResult:
        yield Container(
            Static(STRINGS[self.lang]["dry_run_text"].format(command=self.command), classes="dryrun-message"),
            Horizontal(
                Button("OK", variant="primary", id="ok"),
                classes="dryrun-buttons"
            ),
            classes="dryrun-dialog"
        )

    def on_button_pressed(self, event):
        self.dismiss()
