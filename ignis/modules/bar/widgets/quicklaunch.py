import os
import subprocess
import tempfile
from ignis import widgets
from gi.repository import Gtk, GdkPixbuf
from user_settings import user_settings

_LOCALSEND_SVG = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../assets/localsend.svg")
)
_LOCALSEND_TEMPLATE = open(_LOCALSEND_SVG).read()


def _localsend_pixbuf(size: int = 40) -> GdkPixbuf.Pixbuf:
    svg = _LOCALSEND_TEMPLATE.replace("currentColor", "#ffffff")
    loader = GdkPixbuf.PixbufLoader()
    loader.set_size(size, size)
    loader.write(svg.encode())
    loader.close()
    return loader.get_pixbuf()


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

        _img = Gtk.Image()
        _img.set_from_pixbuf(_localsend_pixbuf(40))

        localsend = widgets.Button(
            css_classes=["launcher-button"],
            tooltip_text="LocalSend",
            child=widgets.Box(child=[_img], halign="center", valign="center"),
            on_click=lambda _: subprocess.Popen(
                ["flatpak", "run", "org.localsend.localsend_app"],
                start_new_session=True,
            ),
            hexpand=True,
            vexpand=True,
            halign="fill",
            valign="fill",
        )

        ql = user_settings.interface.quicklaunch
        chrome.set_visible(ql.show_chrome)
        gemini.set_visible(ql.show_ai)
        localsend.set_visible(ql.show_localsend)

        self.box = widgets.Box(
            css_classes=["quicklaunch", "pill-group"],
            child=[chrome, gemini, localsend],
            spacing=0,
            visible=ql.enabled,
        )

        ql.connect_option("enabled", lambda: self.box.set_visible(ql.enabled))
        ql.connect_option("show_chrome", lambda: chrome.set_visible(ql.show_chrome))
        ql.connect_option("show_ai", lambda: gemini.set_visible(ql.show_ai))
        ql.connect_option("show_localsend", lambda: localsend.set_visible(ql.show_localsend))

    def widget(self):
        return self.box
