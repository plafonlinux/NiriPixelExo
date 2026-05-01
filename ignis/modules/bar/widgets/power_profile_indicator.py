import subprocess
import asyncio
from gi.repository import GLib
from ignis import widgets, utils


_PROFILES = ["performance", "balanced", "power-saver"]

_ICONS = {
    "performance": "bolt",
    "balanced":    "balance",
    "power-saver": "energy_savings_leaf",
}

_TOOLTIPS = {
    "performance": "Производительность",
    "balanced":    "Сбалансированный",
    "power-saver": "Экономия энергии",
}


def _get_profile() -> str:
    try:
        return subprocess.check_output(
            ["powerprofilesctl", "get"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


class PowerProfileIndicator:
    def __init__(self):
        self._current: str = ""

        self._icon_label = widgets.Label(
            label="", css_classes=["power-profile-icon", "m3-icon"]
        )

        self._button = widgets.Button(
            css_classes=["power-profile-indicator"],
            child=self._icon_label,
            on_click=lambda _: self._cycle(),
        )

        self._update()
        GLib.timeout_add_seconds(3, self._update)

    def _apply(self, profile: str):
        self._current = profile
        self._icon_label.set_label(_ICONS.get(profile, ""))
        self._button.set_tooltip_text(_TOOLTIPS.get(profile, profile))

    def _update(self) -> bool:
        profile = _get_profile()
        if profile != self._current:
            self._apply(profile)
        return True

    def _cycle(self):
        try:
            next_profile = _PROFILES[(_PROFILES.index(self._current) + 1) % len(_PROFILES)]
        except ValueError:
            next_profile = _PROFILES[0]
        self._apply(next_profile)
        asyncio.create_task(utils.exec_sh_async(f"powerprofilesctl set {next_profile}"))

    def widget(self):
        return self._button
