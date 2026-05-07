"""TUI entry point for awesome-welcome."""
import sys
import subprocess

from awesome_welcome import config


def run_tui(services_mode=False):
    """Launch the Textual TUI for AI Services Management."""
    config.UI_MODE = "tui"

    # Auto-install textual if missing
    try:
        import textual  # noqa: F401
    except ImportError:
        print("Textual library is missing. Setting up TUI dependencies...")
        try:
            import pip  # noqa: F401
        except ImportError:
            print("Pip not found. Bootstrapping...")
            try:
                subprocess.check_call([sys.executable, "-m", "ensurepip", "--default-pip"])
                import pip  # noqa: F401
            except Exception:
                print("Hiba: A 'python-pip' csomag hi\u00e1nyzik. K\u00e9rlek futtasd: sudo pacman -S python-pip")
                sys.exit(1)
        print("Installing Textual with system override...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "textual", "--break-system-packages"])
            print("Installation complete. Launching TUI...")
        except Exception as e:
            print(f"Failed to install textual: {e}")
            sys.exit(1)

    from awesome_welcome.tui.app import AIServicesManagerTUI
    app = AIServicesManagerTUI()
    app.run()
