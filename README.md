# Awesome Welcome – AI Services Manager Edition

A GTK3 welcome application and **AI Services Manager** for **Manjaro Awesome Respin**.  
Provides quick access to system setup tools and manages local AI/ML services — with both GUI and TUI interfaces.

## Features

### Welcome Screen
- Detects whether running in **Live ISO** or **installed system**.
- Launches **Calamares installer** in live environment.
- Installs **Nordic wallpapers** on installed systems.
- Quick access to **Pamac software manager**.
- Autostart management via toggle switch.

### AI Services Manager
- Manage **Kohya_ss** (LoRA training) — GPU/CPU mode, Byobu session inspect.
- Manage **Stable Diffusion WebUI Forge** — install recommended extensions.
- Manage **ComfyUI** — node-based Stable Diffusion workflow.
- Manage **Ollama** — local LLM inference with Dockge web UI.
- Manage **Docker & Dockge** — container orchestration.
- Real-time **systemd service status** monitoring (active/inactive, enabled/disabled).
- Install, start, stop, restart, enable/disable services from one interface.
- Open service directories in **Midnight Commander**.

### Interface
- **GTK3 GUI** with Nord color theme (when DISPLAY is available).
- **Textual TUI** for terminal/SSH sessions (auto-detected or forced with `--tui`).
- **Bilingual** interface — English and Hungarian, switchable at runtime.
- Smart environment detection: GUI on desktop, TUI over SSH or in TTY.

## Usage

```bash
# Default: auto-detect GUI or TUI
awesome-welcome

# Force TUI mode
awesome-welcome --tui

# Open directly into AI Services Manager
awesome-welcome --services

# Dry-run mode (shows commands without executing)
awesome-welcome --test

# Combine flags
awesome-welcome --tui --services --test
```

## Installation

### From AUR / PKGBUILD

The package name is `awesome-welcome-ai`. It installs the application as `awesome-welcome` to `/usr/bin/awesome-welcome`.

> **Note:** This package conflicts with `awesome-welcome` (main branch version). Only one can be installed at a time.

### Dependencies

| Package | Required | Purpose |
|---|---|---|
| `python` | Yes | Runtime |
| `gtk3` | Yes | GUI toolkit |
| `python-gobject` | Yes | GTK3 Python bindings |
| `python-textual` | Optional | TUI mode support |

## Managed Services

| Service | Path | Systemd Unit | Default User |
|---|---|---|---|
| Kohya_ss | `/opt/kohya_ss` | `kohya_ss.service` | `diffusion` |
| SD WebUI Forge | `/opt/stable-diffusion-webui-forge` | `stable-diffusion-webui-forge.service` | `diffusion` |
| ComfyUI | `/opt/ComfyUI` | `comfyui.service` | `diffusion` |
| Ollama | `/opt/ollama` | `ollama.service` | `root` |
| Docker | — | `docker.service` | `root` |

## License

MIT License – see LICENSE file.

## Credits & Support

- Developer: [megvadulthangya](https://github.com/megvadulthangya)
- Nord Theme: [Arctic Ice Studio](https://www.nordtheme.com/)
- Calamares: Universal installer framework
- [Kohya_ss](https://github.com/bmaltais/kohya_ss) | [SD WebUI Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge) | [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | [Ollama](https://ollama.com/) | [Dockge](https://github.com/louislam/dockge)

For issues or support: [GitHub Issues](https://github.com/megvadulthangya/awesome-welcome/issues)
