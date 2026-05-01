from ignis import widgets
from ignis.services.niri import NiriService

_niri = NiriService.get_default()


class KeyboardLayout:
    def __init__(self):
        self._label = widgets.Label(
            css_classes=["keyboard-layout-text"],
            label=self._current(),
        )
        self._button = widgets.Button(
            child=self._label,
            css_classes=["keyboard-layout", "flat"],
            on_click=lambda _: _niri.keyboard_layouts.switch_layout("Next"),
        )
        _niri.keyboard_layouts.connect("notify::current-name", self._on_change)
        self._on_change()

    _ABBR = {
        "English (US)": "US",
        "Russian": "RU",
    }

    _TOOLTIP = {
        "English (US)": "Английский",
        "Russian": "Русский",
    }

    def _current_name(self) -> str:
        try:
            return _niri.keyboard_layouts.current_name
        except Exception:
            return ""

    def _current(self) -> str:
        name = self._current_name()
        return self._ABBR.get(name, name[:2].upper()) if name else "??"

    def _on_change(self, *_):
        name = self._current_name()
        self._label.set_label(self._ABBR.get(name, name[:2].upper()) if name else "??")
        self._button.set_tooltip_text(self._TOOLTIP.get(name, name))

    def widget(self):
        return self._button
