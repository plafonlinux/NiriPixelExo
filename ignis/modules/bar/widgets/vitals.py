import subprocess
import threading
from gi.repository import GLib
from ignis import widgets


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


_TEMP_DEAD_ZONE = 1.0  # °C
_PWR_DEAD_ZONE  = 5    # W


class Vitals:
    def __init__(self):
        self._mesa = "..."
        self._pwr_history: list[int] = []

        self._cpu_shown: str = "--"
        self._gpu_shown: str = "--"
        self._ssd_shown: str = "--"
        self._pwr_shown: int = -1

        self._label = widgets.Label(
            label="CPU --C  GPU --C  SSD --C  0W  ...",
            css_classes=["vitals-text"],
        )

        self._button = widgets.Button(
            child=self._label,
            css_classes=["vitals"],
            tooltip_text="Системный монитор",
            on_click=lambda _: subprocess.Popen(["kitty", "-e", "btop"]),
        )

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

        text = f"CPU {self._cpu_shown}C  GPU {self._gpu_shown}C  SSD {self._ssd_shown}C  {self._pwr_shown}W  {self._mesa}"
        self._label.set_label(text)

        try:
            is_hot = self._cpu_shown != "--" and float(self._cpu_shown) > 75
        except ValueError:
            is_hot = False

        if is_hot:
            self._button.add_css_class("vitals-hot")
        else:
            self._button.remove_css_class("vitals-hot")

        return True

    def widget(self):
        return self._button
