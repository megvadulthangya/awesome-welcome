"""TUI application (Textual App)."""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.binding import Binding

from awesome_welcome.config import NORD_COLORS
from awesome_welcome.models import ServiceType, SERVICE_REGISTRY
from awesome_welcome.i18n import LanguageManager
from awesome_welcome.tui.widgets import ServiceWidget, DockerWidget, DockgeWidget


class AIServicesManagerTUI(App):
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "back", "Back"),
        Binding("l", "toggle_language", "Toggle Language"),
        Binding("up,left", "focus_previous", "Previous"),
        Binding("down,right,tab", "focus_next", "Next"),
    ]

    CSS = f"""
    Screen {{
        background: {NORD_COLORS['dark0']};
    }}
    Header {{
        background: {NORD_COLORS['dark1']};
        color: {NORD_COLORS['light2']};
    }}
    Footer {{
        background: {NORD_COLORS['dark1']};
        color: {NORD_COLORS['light2']};
    }}
    TabbedContent, TabPane {{
        height: 1fr;
    }}
    .service-panel {{
        border: solid {NORD_COLORS['dark3']};
        background: {NORD_COLORS['dark1']};
        margin: 1;
        padding: 1;
        height: 1fr;
        overflow-y: auto;
        overflow-x: hidden;
    }}
    .title-row {{
        height: auto;
        width: 1fr;
    }}
    .service-title {{
        color: {NORD_COLORS['frost1']};
        text-style: bold;
        width: 1fr;
    }}
    .service-status {{
        color: {NORD_COLORS['green']};
        width: auto;
    }}
    .service-info {{
        color: $text-muted;
        margin: 1 2;
        text-style: italic;
        height: auto;
        width: 1fr;
    }}
    .button-row {{
        layout: grid;
        grid-size: 3;
        grid-gutter: 0 1;
        height: auto;
        width: 1fr;
        margin-top: 1;
    }}
    .button-row Button {{
        width: 1fr;
        margin: 0;
    }}
    Button {{
        background: {NORD_COLORS['dark3']};
        color: {NORD_COLORS['light2']};
        margin: 1;
    }}
    Button:hover {{
        background: {NORD_COLORS['frost3']};
    }}
    ModalScreen {{
        align: center middle;
    }}
    .dialog {{
        background: {NORD_COLORS['dark1']};
        border: thick {NORD_COLORS['red']};
        padding: 1 2;
        width: auto;
        height: auto;
        max-width: 90%;
        max-height: 90%;
    }}
    .dialog-message {{
        color: {NORD_COLORS['light1']};
        padding: 0 1;
        height: auto;
        width: auto;
    }}
    .dialog-buttons {{
        margin-top: 1;
        height: auto;
        width: auto;
        align: center middle;
    }}
    .dryrun-dialog {{
        background: {NORD_COLORS['dark1']};
        border: thick {NORD_COLORS['frost1']};
        padding: 1 2;
        width: auto;
        height: auto;
        max-width: 90%;
        max-height: 90%;
    }}
    .dryrun-message {{
        color: {NORD_COLORS['light1']};
        padding: 1;
    }}
    .dryrun-buttons {{
        margin-top: 1;
        align: center middle;
    }}
    .ext-dialog {{
        background: {NORD_COLORS['dark1']};
        border: thick {NORD_COLORS['frost1']};
        padding: 2;
        margin: 2 4;
        height: 90%;
        width: 90%;
    }}
    .ext-title {{
        color: {NORD_COLORS['frost1']};
        text-style: bold;
        padding: 1;
    }}
    .ext-list {{
        height: 1fr;
        margin: 1;
    }}
    .ext-buttons {{
        margin-top: 1;
        align: center middle;
    }}
    Checkbox.-on {{
        color: {NORD_COLORS['green']};
        text-style: bold;
    }}
    Checkbox > .toggle--button {{
        color: {NORD_COLORS['green']};
    }}
    """

    def __init__(self):
        super().__init__()
        self.lang = LanguageManager("en")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with TabbedContent():
            for st in [ServiceType.KOHYA, ServiceType.FORGE, ServiceType.COMFY, ServiceType.OLLAMA]:
                profile = SERVICE_REGISTRY[st]
                with TabPane(self.lang.t(profile.display_name_key), id=st.value):
                    yield ServiceWidget(st, self.lang)
            with TabPane(self.lang.t("service_docker"), id="docker"):
                yield DockerWidget(self.lang)
            with TabPane(self.lang.t("service_dockge"), id="dockge"):
                yield DockgeWidget(self.lang)

    def on_mount(self):
        self.set_interval(5, self.refresh_all)
        self.refresh_all()

    def refresh_all(self):
        for tab_id in ["kohya", "forge", "comfy", "ollama"]:
            try:
                pane = self.query_one(f"#{tab_id}")
                widget = pane.query_one(ServiceWidget)
                widget.update_status()
            except Exception:
                pass
        try:
            pane = self.query_one("#docker")
            pane.query_one(DockerWidget).update_status()
        except Exception:
            pass
        try:
            pane = self.query_one("#dockge")
            pane.query_one(DockgeWidget).update_status()
        except Exception:
            pass

    def action_toggle_language(self):
        self.lang.toggle()
        panes = list(self.query(TabPane))
        for pane in panes:
            if pane.id in ["kohya", "forge", "comfy", "ollama"]:
                st = ServiceType(pane.id)
                profile = SERVICE_REGISTRY[st]
                pane.label = self.lang.t(profile.display_name_key)
            elif pane.id == "docker":
                pane.label = self.lang.t("service_docker")
            elif pane.id == "dockge":
                pane.label = self.lang.t("service_dockge")
        self.refresh_all()

    def action_quit(self):
        self.exit()

    def action_back(self):
        self.exit()
