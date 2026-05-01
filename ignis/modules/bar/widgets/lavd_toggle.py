import subprocess
import asyncio
from gi.repository import GLib
from ignis import widgets, utils


def _is_active() -> bool:
    try:
        out = subprocess.check_output(
            ["systemctl", "is-active", "scx_lavd.service"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return out == "active"
    except Exception:
        return False


class LAVDToggle:
    def __init__(self):
        self._active = False

        self._icon_label = widgets.Label(
            label="developer_board", css_classes=["lavd-icon", "m3-icon"]
        )

        self._button = widgets.Button(
            css_classes=["lavd-toggle"],
            child=self._icon_label,
            on_click=lambda _: self._toggle(),
        )

        self._update()
        GLib.timeout_add_seconds(3, self._update)

    def _apply(self, active: bool):
        self._active = active
        if active:
            self._button.add_css_class("active")
            self._button.set_tooltip_text("LAVD: включён")
        else:
            self._button.remove_css_class("active")
            self._button.set_tooltip_text("LAVD: выключен")

    def _update(self) -> bool:
        active = _is_active()
        if active != self._active:
            self._apply(active)
        return True

    def _toggle(self):
        next_state = not self._active
        self._apply(next_state)
        cmd = "systemctl start scx_lavd.service" if next_state else "systemctl stop scx_lavd.service"
        asyncio.create_task(utils.exec_sh_async(cmd))

    def widget(self):
        return self._button
