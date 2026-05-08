"""TUI modal dialogs."""
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.containers import Container, Horizontal
from textual.app import ComposeResult

from awesome_welcome.i18n import STRINGS  # noqa: F401


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


class ExtensionsSelectModal(ModalScreen):
    """Modal dialog for selecting Forge extensions to install."""
    def __init__(self, lang_mgr):
        super().__init__()
        self.lang = lang_mgr

    def compose(self) -> ComposeResult:
        from textual.widgets import Checkbox
        from textual.containers import ScrollableContainer
        from awesome_welcome.services.forge import FORGE_EXTENSIONS

        with Container(classes="ext-dialog"):
            yield Static(self.lang.t("ext_dialog_title"), classes="ext-title")
            with ScrollableContainer(classes="ext-list"):
                for ext in FORGE_EXTENSIONS:
                    yield Checkbox(ext["name"], value=True, id=f"ext-{ext['name']}")
            with Horizontal(classes="ext-buttons"):
                yield Button(self.lang.t("ext_select_all"), id="ext-all")
                yield Button(self.lang.t("ext_deselect_all"), id="ext-none")
                yield Button(self.lang.t("ext_install_selected"), variant="primary", id="ext-install")
                yield Button(self.lang.t("ext_cancel"), id="ext-cancel")

    def on_button_pressed(self, event: Button.Pressed):
        from textual.widgets import Checkbox
        from awesome_welcome.services.forge import FORGE_EXTENSIONS

        if event.button.id == "ext-all":
            for cb in self.query(Checkbox):
                cb.value = True
        elif event.button.id == "ext-none":
            for cb in self.query(Checkbox):
                cb.value = False
        elif event.button.id == "ext-install":
            selected = []
            for ext in FORGE_EXTENSIONS:
                try:
                    cb = self.query_one(f"#ext-{ext['name']}", Checkbox)
                    if cb.value:
                        selected.append(ext)
                except Exception:
                    pass
            self.dismiss(selected)
        elif event.button.id == "ext-cancel":
            self.dismiss(None)


class ForgeVersionSelectModal(ModalScreen):
    """Modal for selecting Forge version to install."""
    def __init__(self, lang_mgr):
        super().__init__()
        self.lang = lang_mgr

    def compose(self) -> ComposeResult:
        from textual.widgets import RadioButton, RadioSet
        with Container(classes="dialog"):
            yield Static(self.lang.t("forge_purge_warning"), classes="dialog-message")
            with RadioSet(id="forge-version-set"):
                yield RadioButton(self.lang.t("forge_version_forge"), id="pkg-forge", value=True)
                yield RadioButton(self.lang.t("forge_version_cu124"), id="pkg-cu124")
                yield RadioButton(self.lang.t("forge_version_neo"), id="pkg-neo")
            with Horizontal(classes="dialog-buttons"):
                yield Button("OK", variant="primary", id="ok")
                yield Button(self.lang.t("ext_cancel"), id="cancel")

    def on_button_pressed(self, event: Button.Pressed):
        from textual.widgets import RadioSet
        if event.button.id == "ok":
            radio_set = self.query_one("#forge-version-set", RadioSet)
            pressed = radio_set.pressed_button
            pkg_map = {
                "pkg-forge": "stable-diffusion-webui-forge",
                "pkg-cu124": "stable-diffusion-webui-forge-cu124",
                "pkg-neo": "stable-diffusion-webui-forge-neo-git",
            }
            self.dismiss(pkg_map.get(pressed.id) if pressed else None)
        elif event.button.id == "cancel":
            self.dismiss(None)
