import os
import subprocess
import tempfile
from ignis import widgets


def _open_ai_tabs(_):
    session = "new_tab Gemini\nlaunch gemini\nnew_tab Claude\nlaunch claude\n"
    fd, path = tempfile.mkstemp(suffix=".kitty")
    try:
        os.write(fd, session.encode())
    finally:
        os.close(fd)
    subprocess.Popen(["kitty", "--session", path], start_new_session=True)


class QuickLaunch:
    def __init__(self):
        chrome = widgets.Button(
            label="󰖟",
            css_classes=["m3-icon", "launcher-button"],
            tooltip_text="Google Chrome",
            on_click=lambda _: subprocess.Popen(
                ["flatpak", "run", "com.google.Chrome"]
            ),
            hexpand=True,
            vexpand=True,
            halign="fill",
            valign="fill",
        )

        gemini = widgets.Button(
            label="󱜙",
            css_classes=["m3-icon", "launcher-button"],
            tooltip_text="Gemini + Claude",
            on_click=_open_ai_tabs,
            hexpand=True,
            vexpand=True,
            halign="fill",
            valign="fill",
        )

        self.box = widgets.Box(
            css_classes=["quicklaunch", "pill-group"],
            child=[chrome, gemini],
            spacing=0,
        )

    def widget(self):
        return self.box
