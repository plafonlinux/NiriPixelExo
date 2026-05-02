import subprocess
import asyncio
import os
from gi.repository import GLib
from ignis import widgets, utils
from ignis.services.network import NetworkService
from user_settings import user_settings


network = NetworkService.get_default()
_RFKILL = "/usr/sbin/rfkill"


def _wifi_icon(enabled: bool, connected: bool) -> str:
    if not enabled:
        return "wifi_off"
    return "wifi" if connected else "wifi_find"


def _wifi_subtitle(enabled: bool, connected: bool) -> str:
    if not enabled:
        return "Выключен"
    return "Подключён" if connected else "Не подключён"


def _bt_subtitle(powered: bool) -> str:
    return "Включён" if powered else "Выключен"


def _bt_powered() -> bool:
    try:
        for name in os.listdir("/sys/class/rfkill/"):
            dev = f"/sys/class/rfkill/{name}"
            if open(f"{dev}/name").read().strip().startswith("hci"):
                return (
                    open(f"{dev}/state").read().strip() == "1"
                    and open(f"{dev}/soft").read().strip() == "0"
                )
    except Exception:
        pass
    return False


def _bt_available() -> bool:
    try:
        return any(
            open(f"/sys/class/rfkill/{n}/name").read().strip().startswith("hci")
            for n in os.listdir("/sys/class/rfkill/")
        )
    except Exception:
        return False


def _open_wifi_settings():
    env = os.environ.copy()
    env["XDG_CURRENT_DESKTOP"] = "GNOME"
    subprocess.Popen(["gnome-control-center", "wifi"], env=env)


def _open_bt_settings():
    subprocess.Popen(["blueman-manager"])


class LauncherTile(widgets.Button):
    def __init__(self, icon: str, label: str, subtitle: str, command: list, env: dict | None = None):
        super().__init__(
            css_classes=["quick-tile", "button"],
            hexpand=True,
            child=widgets.Box(
                spacing=8,
                child=[
                    widgets.Label(css_classes=["qt-icon", "m3-icon"], label=icon),
                    widgets.Box(
                        vertical=True,
                        spacing=2,
                        halign="start",
                        child=[
                            widgets.Label(css_classes=["qt-title"], label=label, halign="start"),
                            widgets.Label(css_classes=["qt-subtitle"], label=subtitle, halign="start"),
                        ],
                    ),
                ],
            ),
            on_click=lambda _: subprocess.Popen(command, start_new_session=True, env=env),
        )


class WiFiTile(widgets.Box):
    def __init__(self):
        wifi = network.wifi

        self._icon_label = widgets.Label(css_classes=["qt-icon", "m3-icon"], label="")
        self._subtitle_label = widgets.Label(css_classes=["qt-subtitle"], label="", halign="start")

        self._main_btn = widgets.Button(
            css_classes=["qt-main"],
            hexpand=True,
            child=widgets.Box(
                spacing=8,
                child=[
                    self._icon_label,
                    widgets.Box(
                        vertical=True,
                        spacing=2,
                        halign="start",
                        child=[
                            widgets.Label(label="Wi-Fi", css_classes=["qt-title"], halign="start"),
                            self._subtitle_label,
                        ],
                    ),
                ],
            ),
            on_click=lambda _: setattr(network.wifi, "enabled", not network.wifi.enabled),
        )

        self._arrow_btn = widgets.Button(
            css_classes=["qt-arrow"],
            tooltip_text="Настройки Wi-Fi",
            child=widgets.Label(label="chevron_right", css_classes=["m3-icon", "qt-arrow-icon"]),
            on_click=lambda _: _open_wifi_settings(),
        )

        super().__init__(
            css_classes=["quick-tile"],
            hexpand=True,
            child=[self._main_btn, self._arrow_btn],
        )

        wifi.connect("notify::enabled", self._on_changed)
        wifi.connect("notify::is-connected", self._on_changed)
        self._update()

    def _update(self):
        wifi = network.wifi
        on, conn = wifi.enabled, wifi.is_connected
        self._icon_label.set_label(_wifi_icon(on, conn))
        self._subtitle_label.set_label(_wifi_subtitle(on, conn))
        classes = [c for c in self.get_css_classes() if c != "active"]
        if on:
            classes.append("active")
        self.set_css_classes(classes)

    def _on_changed(self, *_):
        self._update()


class BtTile(widgets.Box):
    def __init__(self):
        self._powered = False

        self._icon_label = widgets.Label(css_classes=["qt-icon", "m3-icon"], label="")
        self._subtitle_label = widgets.Label(css_classes=["qt-subtitle"], label="", halign="start")

        self._main_btn = widgets.Button(
            css_classes=["qt-main"],
            hexpand=True,
            child=widgets.Box(
                spacing=8,
                child=[
                    self._icon_label,
                    widgets.Box(
                        vertical=True,
                        spacing=2,
                        halign="start",
                        child=[
                            widgets.Label(label="Bluetooth", css_classes=["qt-title"], halign="start"),
                            self._subtitle_label,
                        ],
                    ),
                ],
            ),
            on_click=lambda _: self._toggle(),
        )

        self._arrow_btn = widgets.Button(
            css_classes=["qt-arrow"],
            tooltip_text="Blueman",
            child=widgets.Label(label="chevron_right", css_classes=["m3-icon", "qt-arrow-icon"]),
            on_click=lambda _: _open_bt_settings(),
        )

        super().__init__(
            css_classes=["quick-tile"],
            hexpand=True,
            child=[self._main_btn, self._arrow_btn],
        )

        self._poll()
        GLib.timeout_add_seconds(3, self._poll)

    def _poll(self) -> bool:
        on = _bt_powered()
        if on != self._powered:
            self._apply(on)
        return True

    def _apply(self, on: bool):
        self._powered = on
        self._icon_label.set_label("bluetooth" if on else "bluetooth_disabled")
        self._subtitle_label.set_label(_bt_subtitle(on))
        classes = [c for c in self.get_css_classes() if c != "active"]
        if on:
            classes.append("active")
        self.set_css_classes(classes)

    def _toggle(self):
        cmd = f"{_RFKILL} unblock bluetooth" if not self._powered else f"{_RFKILL} block bluetooth"
        self._apply(not self._powered)
        asyncio.create_task(utils.exec_sh_async(cmd))


class QuickToggles(widgets.Box):
    def __init__(self):
        qt = user_settings.interface.quicktoggles

        wifi_tile = WiFiTile()
        wifi_tile.set_visible(qt.show_wifi)

        bt_tile = BtTile()
        bt_tile.set_visible(qt.show_bluetooth and _bt_available())

        tuner_tile = LauncherTile(
            icon="tune",
            label="Тюнер",
            subtitle="Управление системой",
            command=["tuner"],
        )
        tuner_tile.set_visible(qt.show_tuner)

        gnome_tile = LauncherTile(
            icon="settings_applications",
            label="Настройки GNOME",
            subtitle="Системные",
            command=["gnome-control-center"],
            env={**os.environ, "XDG_CURRENT_DESKTOP": "GNOME"},
        )
        gnome_tile.set_visible(qt.show_gnome_settings)

        thunderbird_tile = LauncherTile(
            icon="mail",
            label="Thunderbird",
            subtitle="Почта",
            command=["flatpak", "run", "org.mozilla.Thunderbird"],
        )
        thunderbird_tile.set_visible(qt.show_thunderbird)

        bitwarden_tile = LauncherTile(
            icon="lock",
            label="Bitwarden",
            subtitle="Пароли",
            command=["flatpak", "run", "com.bitwarden.desktop"],
        )
        bitwarden_tile.set_visible(qt.show_bitwarden)

        row1 = widgets.Box(
            css_classes=["quick-tiles-row"],
            hexpand=True,
            homogeneous=True,
            spacing=8,
            child=[wifi_tile, bt_tile],
            visible=(qt.show_wifi or (qt.show_bluetooth and _bt_available())),
        )
        row2 = widgets.Box(
            css_classes=["quick-tiles-row"],
            hexpand=True,
            homogeneous=True,
            spacing=8,
            child=[tuner_tile, gnome_tile],
            visible=(qt.show_tuner or qt.show_gnome_settings),
        )
        row3 = widgets.Box(
            css_classes=["quick-tiles-row"],
            hexpand=True,
            homogeneous=True,
            spacing=8,
            child=[thunderbird_tile, bitwarden_tile],
            visible=(qt.show_thunderbird or qt.show_bitwarden),
        )

        super().__init__(
            vertical=True,
            spacing=8,
            child=[row1, row2, row3],
        )

        def _refresh_row1(*_):
            wifi_tile.set_visible(qt.show_wifi)
            bt_tile.set_visible(qt.show_bluetooth and _bt_available())
            row1.set_visible(qt.show_wifi or (qt.show_bluetooth and _bt_available()))

        def _refresh_row2(*_):
            tuner_tile.set_visible(qt.show_tuner)
            gnome_tile.set_visible(qt.show_gnome_settings)
            row2.set_visible(qt.show_tuner or qt.show_gnome_settings)

        def _refresh_row3(*_):
            thunderbird_tile.set_visible(qt.show_thunderbird)
            bitwarden_tile.set_visible(qt.show_bitwarden)
            row3.set_visible(qt.show_thunderbird or qt.show_bitwarden)

        qt.connect("notify::show-wifi", _refresh_row1)
        qt.connect("notify::show-bluetooth", _refresh_row1)
        qt.connect("notify::show-tuner", _refresh_row2)
        qt.connect("notify::show-gnome-settings", _refresh_row2)
        qt.connect("notify::show-thunderbird", _refresh_row3)
        qt.connect("notify::show-bitwarden", _refresh_row3)
