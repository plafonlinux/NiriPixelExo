import subprocess
import threading
from ignis import widgets
from gi.repository import GLib
from scripts.altbooster_bridge import get_updates_count, force_refresh_updates


class UpdatesIndicator:
    def __init__(self):
        self._count = 0

        self._icon = widgets.Label(
            label="verified",
            css_classes=["updates-icon"],
        )
        self._badge = widgets.Label(
            label="",
            css_classes=["updates-badge"],
            visible=False,
        )

        self._button = widgets.Button(
            child=widgets.Box(
                spacing=2,
                child=[self._icon, self._badge],
            ),
            css_classes=["updates-indicator", "updates-ok"],
            tooltip_text="Система обновлена",
            on_click=lambda _: subprocess.Popen(
                ["altbooster", "-s"], start_new_session=True
            ),
        )

        GLib.timeout_add_seconds(30, self._first_check)

    def _first_check(self):
        self._check()

        def periodic():
            self._check()
            return True

        GLib.timeout_add_seconds(3 * 3600, periodic)
        return False

    def _check(self):
        threading.Thread(target=self._check_thread, daemon=True).start()

    def _check_thread(self):
        data = get_updates_count()
        GLib.idle_add(self._apply, data)

    def _apply(self, data: dict):
        self._count = data.get("count", 0)
        if self._count == 0:
            self._icon.set_label("verified")
            self._badge.set_visible(False)
            self._button.set_css_classes(["updates-indicator", "updates-ok"])
            self._button.set_tooltip_text("Система обновлена")
        else:
            self._icon.set_label("system_update_alt")
            self._badge.set_label(str(self._count))
            self._badge.set_visible(True)
            self._button.set_css_classes(["updates-indicator", "updates-available"])
            self._button.set_tooltip_text(f"Доступно {self._count} обновлений")

    def widget(self):
        return self._button
