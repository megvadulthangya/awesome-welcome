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
"""
