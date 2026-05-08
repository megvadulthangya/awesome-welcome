"""SD WebUI Forge service helpers."""


def _forge_extensions_install_command():
    """Return shell command to install recommended SD Forge extensions directly."""
    extensions_dir = "/opt/stable-diffusion-webui-forge/extensions"
    cmds = [
        f"mkdir -p {extensions_dir}",
        f"cd {extensions_dir}",
        "git clone https://github.com/Mikubill/sd-webui-controlnet.git",
        "git clone https://github.com/continue-revolution/sd-webui-segment-anything.git",
        "git clone https://github.com/Bing-su/adetailer.git",
        "git clone https://github.com/pkuliyi2015/multidiffusion-upscaler-for-automatic1111.git",
        "git clone https://github.com/huchenlei/sd-webui-openpose-editor.git",
        "git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui-rembg.git",
    ]
    return " && ".join(cmds)
