import subprocess
import threading
from ignis import widgets
from gi.repository import GLib
from scripts.altbooster_bridge import get_backup_status, force_refresh_backup


class BackupIndicator:
    def __init__(self):
        self._status = None

        self._icon = widgets.Label(
            label="cloud_sync",
            css_classes=["backup-icon"],
        )
        self._label = widgets.Label(
            label="",
            css_classes=["backup-text"],
        )

        self._button = widgets.Button(
            child=widgets.Box(
                spacing=4,
                child=[self._icon, self._label],
            ),
            css_classes=["backup-indicator"],
            visible=False,
            on_click=lambda _: subprocess.Popen(
                ["altbooster", "-t"], start_new_session=True
            ),
        )

        GLib.timeout_add_seconds(10, self._first_check)

    def _first_check(self):
        self._check()

        def periodic():
            self._check()
            return True

        GLib.timeout_add_seconds(30 * 60, periodic)
        return False

    def _check(self):
        threading.Thread(target=self._check_thread, daemon=True).start()

    def _check_thread(self):
        data = get_backup_status()
        GLib.idle_add(self._apply, data)

    def _apply(self, data: dict | None):
        if data is None:
            self._button.set_visible(False)
            return

        self._button.set_visible(True)
        last = data.get("last", "")
        self._label.set_label(last)

        tt = f"Последний бэкап: {last}"
        nxt = data.get("next")
        if nxt:
            tt += f"\nСледующий: {nxt}"
        self._button.set_tooltip_text(tt)

    def widget(self):
        return self._button
