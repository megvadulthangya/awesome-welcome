# Testing awesome-welcome TUI Mode

## Overview

The `awesome-welcome` app is a Manjaro AI Services Manager with both TUI (Textual) and GUI (GTK3) modes. This skill covers testing the TUI mode end-to-end after code changes.

## Prerequisites

- Python 3.x with `textual` package installed (`pip install textual`)
- No special secrets needed for TUI testing
- GTK3/PyGObject is required only for GUI mode testing (often unavailable on non-Manjaro systems)

## Devin Secrets Needed

None — TUI testing requires no credentials or secrets.

## Running the App

```bash
cd ~/awesome-welcome

# TUI mode (force even if DISPLAY is set)
python3 -m awesome_welcome --tui

# Dry-run mode (shows commands instead of executing)
python3 -m awesome_welcome --test --tui

# Via launcher script
./awesome-welcome --tui
./awesome-welcome --test --tui

# Help
python3 -m awesome_welcome --help
```

## Key Test Scenarios

### 1. Entry Points
- `python3 -m awesome_welcome --help` should show argparse help with `--test`, `--tui`, `--services` options
- `./awesome-welcome --help` should produce identical output
- Both entry points must resolve all cross-module imports without errors

### 2. TUI Launch & Tabs
- Launch with `--tui` flag (required when DISPLAY is set, otherwise TUI may try GUI mode)
- Verify 5 service tabs render: Kohya_ss, SD WebUI Forge, ComfyUI, Ollama, Docker & Dockge
- Each tab should show its service panel with appropriate buttons
- Header shows "AIServicesManagerTUI", footer shows keybindings

### 3. Tab Navigation
- Use Right/Left arrow keys to navigate between tabs
- Each tab should render its respective ServiceWidget or DockerWidget

### 4. Language Toggle
- Press `l` to toggle between English and Hungarian
- Verify button labels change (e.g., "Enable at startup" → "Engedélyezés induláskor")
- Status text changes (e.g., "Not installed" → "Nincs telepítve")
- Note: Docker & Dockge tab may not show all translated labels (DockerWidget has some hardcoded labels)

### 5. Dry-Run Modal
- Launch with `--test --tui` flags
- Click any "Install" button
- DryRunModal should appear showing "Would execute:" followed by the actual command
- Click OK to dismiss

### 6. Clean Exit
- Press Ctrl+Q to exit
- Should return to shell prompt with no traceback

## Known Limitations

- **GUI mode cannot be tested** without PyGObject/GTK3 installed. On non-Manjaro systems, GUI modules can only be validated via `python3 -c "import ast; ast.parse(open('file').read())"`
- **Service operations** (Install, Start, Stop) require the target Manjaro environment with systemd services. Only the dry-run path can be tested on generic Linux.
- **DISPLAY variable**: When DISPLAY is set (e.g., `:0`), the app defaults to GUI mode. Always use `--tui` flag to force TUI mode in testing environments.
- **Textual auto-install**: The `tui/__init__.py` has auto-install logic for textual. If textual is missing, it may attempt `pip install textual` automatically.

## Architecture Notes

- Package structure: `awesome_welcome/` with subpackages `config/`, `i18n/`, `models/`, `helpers/`, `services/`, `tui/`, `gui/`
- Global state: `config.DRY_RUN` and `config.UI_MODE` — always access via `from awesome_welcome import config; config.DRY_RUN` pattern
- Lazy imports: GTK3 and Textual are only imported when their respective UI mode is selected
- The launcher script (`awesome-welcome`) inserts repo dir into sys.path
