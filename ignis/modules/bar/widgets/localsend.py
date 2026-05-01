import subprocess
import os
from ignis import widgets
from gi.repository import Gtk, GdkPixbuf
from user_settings import user_settings

_ICON = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../assets/localsend.svg"))
_SVG_TEMPLATE = open(_ICON).read()


def _render_pixbuf(dark: bool) -> GdkPixbuf.Pixbuf:
    color = "#ffffff" if dark else "#1a1a1a"
    svg = _SVG_TEMPLATE.replace("currentColor", color)
    loader = GdkPixbuf.PixbufLoader()
    loader.set_size(16, 16)
    loader.write(svg.encode())
    loader.close()
    return loader.get_pixbuf()


class LocalSendLauncher:
    def __init__(self):
        self._image = Gtk.Image()
        self._image.add_css_class("localsend-icon")
        self._update_icon()

        user_settings.appearance.wallcolors.connect(
            "changed",
            lambda _, name: self._update_icon() if name == "dark_mode" else None,
        )

        self._button = widgets.Button(
            css_classes=["localsend-btn"],
            tooltip_text="LocalSend",
            child=self._image,
            on_click=lambda _: subprocess.Popen(
                ["flatpak", "run", "org.localsend.localsend_app"],
                start_new_session=True,
            ),
        )

    def _update_icon(self):
        pb = _render_pixbuf(user_settings.appearance.wallcolors.dark_mode)
        self._image.set_from_pixbuf(pb)

    def widget(self):
        return self._button
