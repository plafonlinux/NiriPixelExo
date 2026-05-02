import subprocess
import threading
from ignis import widgets
from ignis.menu_model import IgnisMenuModel, IgnisMenuItem, IgnisMenuSeparator
from gi.repository import GLib


def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout
    except Exception:
        return ""


def _read_sensors():
    cpu_t, gpu_t, ssd_t, pwr_w = "--", "--", "--", 0

    for line in _run(["sensors", "k10temp-pci-00c3"]).splitlines():
        if "Tctl" in line:
            cpu_t = line.split()[1].lstrip("+").rstrip("°C")
            break

    for line in _run(["sensors", "amdgpu-pci-c500"]).splitlines():
        if "edge" in line and gpu_t == "--":
            gpu_t = line.split()[1].lstrip("+").rstrip("°C")
        if "PPT:" in line:
            try:
                pwr_w = round(float(line.split()[1]))
            except Exception:
                pass

    for line in _run(["sensors", "nvme-pci-0100"]).splitlines():
        if "Composite" in line:
            ssd_t = line.split()[1].lstrip("+").rstrip("°C")
            break

    return cpu_t, gpu_t, ssd_t, pwr_w


_TEMP_DEAD_ZONE = 1.0
_PWR_DEAD_ZONE = 5


class Vitals:
    def __init__(self):
        self._mesa = "..."
        self._pwr_history: list[int] = []

        self._cpu_shown: str = "--"
        self._gpu_shown: str = "--"
        self._ssd_shown: str = "--"
        self._pwr_shown: int = -1

        self._icon = widgets.Label(
            label="device_thermostat",
            css_classes=["vitals-icon"],
        )
        self._badge = widgets.Label(
            label="",
            css_classes=["vitals-badge"],
            visible=False,
        )

        self._button = widgets.Button(
            child=widgets.Box(
                spacing=2,
                child=[self._icon, self._badge],
            ),
            css_classes=["vitals"],
            tooltip_text="Системный монитор",
        )

        self._button.connect("clicked", self._on_clicked)

        threading.Thread(target=self._fetch_mesa, daemon=True).start()

        GLib.timeout_add_seconds(3, self._update)

    def _fetch_mesa(self):
        out = _run(["eglinfo"])
        for line in out.splitlines():
            if "Mesa " in line and "OpenGL" in line:
                part = line.split("Mesa ")[-1].strip().rstrip(")")
                self._mesa = part.split()[0]
                break
        else:
            self._mesa = "?"
        GLib.idle_add(self._update)

    def _maybe_update_temp(self, new_raw: str, shown: str) -> str:
        try:
            if shown == "--" or abs(float(new_raw) - float(shown)) >= _TEMP_DEAD_ZONE:
                return new_raw
        except (ValueError, TypeError):
            pass
        return shown

    def _on_clicked(self, _btn):
        menu_items = [
            IgnisMenuItem(
                label=f"CPU          {self._cpu_shown}°C",
                icon_name="device_thermostat",
                on_activate=lambda *a: None,
            ),
            IgnisMenuItem(
                label=f"GPU          {self._gpu_shown}°C",
                icon_name="memory",
                on_activate=lambda *a: None,
            ),
            IgnisMenuItem(
                label=f"SSD          {self._ssd_shown}°C",
                icon_name="hard_disk",
                on_activate=lambda *a: None,
            ),
            IgnisMenuItem(
                label=f"Потребление {self._pwr_shown}W",
                icon_name="bolt",
                on_activate=lambda *a: None,
            ),
            IgnisMenuItem(
                label=f"Mesa         {self._mesa}",
                icon_name="display_settings",
                on_activate=lambda *a: None,
            ),
            IgnisMenuSeparator(),
            IgnisMenuItem(
                label="Открыть btop",
                icon_name="monitoring",
                on_activate=lambda *a: subprocess.Popen(
                    ["kitty", "-e", "btop"], start_new_session=True
                ),
            ),
        ]

        model = IgnisMenuModel(*menu_items)
        self._popover = widgets.PopoverMenu(model=model, css_classes=["vitals-popover"])
        self._popover.set_parent(self._button)
        self._popover.popup()

    def _update(self):
        cpu_t, gpu_t, ssd_t, pwr_w = _read_sensors()

        self._cpu_shown = self._maybe_update_temp(cpu_t, self._cpu_shown)
        self._gpu_shown = self._maybe_update_temp(gpu_t, self._gpu_shown)
        self._ssd_shown = self._maybe_update_temp(ssd_t, self._ssd_shown)

        self._pwr_history.append(pwr_w)
        if len(self._pwr_history) > 3:
            self._pwr_history.pop(0)
        avg_pwr = round(sum(self._pwr_history) / len(self._pwr_history))
        if self._pwr_shown < 0 or abs(avg_pwr - self._pwr_shown) >= _PWR_DEAD_ZONE:
            self._pwr_shown = avg_pwr

        is_hot = False
        try:
            cpu_f = float(self._cpu_shown) if self._cpu_shown != "--" else None
            if cpu_f is not None:
                self._badge.set_label(self._cpu_shown)
                self._badge.set_visible(True)
                is_hot = cpu_f > 75
            else:
                self._badge.set_visible(False)
        except (ValueError, TypeError):
            self._badge.set_visible(False)

        if is_hot:
            self._button.add_css_class("vitals-hot")
        else:
            self._button.remove_css_class("vitals-hot")

        return True

    def widget(self):
        return self._button
