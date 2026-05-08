"""GTK3 CSS styling."""
from awesome_welcome.config import NORD_COLORS

CSS_DATA = f"""
window {{ background-color: {NORD_COLORS['dark0']}; color: {NORD_COLORS['light0']}; }}
headerbar {{ background-color: {NORD_COLORS['dark1']}; color: {NORD_COLORS['light2']}; border: none; }}
.action-btn {{ background-color: {NORD_COLORS['frost3']}; color: {NORD_COLORS['light2']}; font-weight: bold; padding: 12px; margin: 5px; }}
.action-btn:hover {{ background-color: {NORD_COLORS['frost2']}; }}
.link-btn {{ background-color: {NORD_COLORS['dark2']}; color: {NORD_COLORS['light0']}; padding: 6px; font-size: 13px; margin: 2px; }}
.link-btn:hover {{ background-color: {NORD_COLORS['dark3']}; }}
label {{ color: {NORD_COLORS['light0']}; font-size: 14px; }}
switch {{ margin-left: 10px; }}
.title-label {{ font-size: 24px; font-weight: bold; color: {NORD_COLORS['frost1']}; margin-bottom: 10px; }}
.desc-label {{ margin-bottom: 20px; color: {NORD_COLORS['light1']}; }}
.section-label {{ font-size: 12px; font-weight: bold; color: {NORD_COLORS['frost0']}; margin-top: 10px; margin-bottom: 5px; }}
.autostart-box {{ margin-top: 15px; border-top: 1px solid {NORD_COLORS['dark3']}; padding-top: 10px; }}
.service-frame {{ border: 1px solid {NORD_COLORS['dark3']}; border-radius: 8px; padding: 10px; margin: 8px; background-color: {NORD_COLORS['dark1']}; }}
.service-title {{ font-size: 16px; font-weight: bold; color: {NORD_COLORS['frost1']}; margin-bottom: 5px; }}
.service-status {{ font-size: 12px; color: {NORD_COLORS['green']}; }}
.service-button {{ background-color: {NORD_COLORS['dark3']}; color: {NORD_COLORS['light2']}; padding: 6px; margin: 2px; font-size: 12px; }}
.service-button:hover {{ background-color: {NORD_COLORS['frost3']}; }}
.warning-label {{ color: {NORD_COLORS['red']}; font-size: 12px; }}
.service-info {{ color: {NORD_COLORS['light1']}; font-size: 12px; margin-top: 4px; margin-bottom: 4px; }}

/*
 * Force-visible indicators for CheckButton (extensions dialog) and RadioButton
 * (Forge switch version dialog). Without these, certain GTK themes render
 * the check / dot indicator with very low contrast or hide it entirely on
 * dark backgrounds, leaving the user without visual feedback for selection.
 */
checkbutton check, radiobutton radio,
checkbutton > check, radiobutton > radio {{
    background-color: {NORD_COLORS['dark2']};
    border: 1px solid {NORD_COLORS['light0']};
    min-height: 16px;
    min-width: 16px;
    margin-right: 6px;
}}
checkbutton check:checked, radiobutton radio:checked,
checkbutton > check:checked, radiobutton > radio:checked {{
    background-color: {NORD_COLORS['green']};
    border: 2px solid {NORD_COLORS['light2']};
    color: {NORD_COLORS['dark0']};
    -gtk-icon-source: -gtk-icontheme("object-select-symbolic");
}}
checkbutton:checked, radiobutton:checked {{
    color: {NORD_COLORS['green']};
    font-weight: bold;
}}

/*
 * Prominent "Open WebUI" row pinned to the bottom of every service tab.
 * The Open button is the main entry point to the running web frontend on
 * each service (Forge:7860 / Comfy:8188 / Kohya:7861 / Ollama:8080 by
 * default), so it gets accent styling. Edit URL is its smaller companion.
 */
.webui-row {{
    margin-top: 10px;
    border-top: 1px solid {NORD_COLORS['dark3']};
    padding-top: 8px;
}}
.webui-url-label {{
    color: {NORD_COLORS['light1']};
    font-size: 11px;
    margin-bottom: 4px;
}}
.webui-open-button {{
    background-color: {NORD_COLORS['frost1']};
    color: {NORD_COLORS['dark0']};
    font-weight: bold;
    padding: 10px;
    font-size: 14px;
    border-radius: 4px;
}}
.webui-open-button:hover {{
    background-color: {NORD_COLORS['frost0']};
}}
.webui-open-button:disabled {{
    background-color: {NORD_COLORS['dark2']};
    color: {NORD_COLORS['dark3']};
}}
.webui-edit-button {{
    background-color: {NORD_COLORS['dark3']};
    color: {NORD_COLORS['light2']};
    padding: 8px;
    font-size: 12px;
    border-radius: 4px;
}}
.webui-edit-button:hover {{
    background-color: {NORD_COLORS['frost3']};
}}
"""
