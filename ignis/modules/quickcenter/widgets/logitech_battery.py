from ignis import widgets
from ignis.services.upower import UPowerService

upower = UPowerService.get_default()


def _device_icon(model: str) -> str:
    m = model.lower()
    if "key" in m:
        return "keyboard"
    if "master" in m or "mouse" in m or "mx" in m:
        return "mouse"
    return "devices"


class _DeviceChip(widgets.Box):
    def __init__(self, dev):
        self._dev = dev
        self._icon = widgets.Label(
            css_classes=["logitech-bat-icon", "m3-icon"],
            style="font-family: 'Material Symbols Outlined', 'Material Icons Outlined'; font-size: 14px;",
        )
        self._label = widgets.Label(css_classes=["logitech-bat-percent"])
        super().__init__(
            spacing=3,
            valign="center",
            halign="center",
            child=[self._icon, self._label],
        )
        self.set_tooltip_text(dev.model or dev.native_path)
        self._update()
        dev.connect("notify::percent", lambda *_: self._update())

    def _update(self):
        self._icon.set_label(_device_icon(self._dev.model or ""))
        pct = self._dev.percent
        self._label.set_label(f"{int(pct)}%" if pct is not None else "–")


class LogitechBattery(widgets.Box):
    def __init__(self):
        super().__init__(spacing=8, valign="center", halign="center")
        self._seen: set = set()

        for dev in upower.devices:
            self._try_add(dev)

        upower.connect("device_added", lambda _, dev: self._try_add(dev))

    def _try_add(self, dev):
        path = dev.native_path or ""
        if "hidpp_battery" in path and path not in self._seen:
            self._seen.add(path)
            self.append(_DeviceChip(dev))
