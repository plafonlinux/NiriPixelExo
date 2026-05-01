import asyncio
import subprocess
import os
from ignis import widgets
from ignis.services.bluetooth import BluetoothService
from modules.m3components import Button
from modules.settings.widgets import CategoryLabel, SettingsRow, SwitchRow
from scripts import send_notification


class BluetoothTab(widgets.Box):
    def __init__(self):
        self.bluetooth_service = BluetoothService.get_default()

        if self.bluetooth_service.state == "absent":
            super().__init__(
                vertical=True,
                spacing=20,
                css_classes=["settings-body"],
                hexpand=False,
                halign="center",
                width_request=800,
                child=[
                    widgets.Label(
                        label="Bluetooth не найден", halign="center", vexpand=True
                    )
                ],
            )
            return

        super().__init__(
            vertical=True,
            spacing=8,
            css_classes=["settings-body"],
            hexpand=False,
            halign="center",
            width_request=800,
        )

        self.adapter_category = self.create_adapter_category()
        self.device_category = self.create_device_category()

        self.append(self.adapter_category)
        self.append(widgets.Separator())
        self.append(self.device_category)

        self.scan_status_label = widgets.Label(label="")
        self.scan_button = Button.button(
            icon="bluetooth_searching",
            label="Поиск устройств",
            on_click=lambda x: asyncio.create_task(self.start_scan()),
        )
        self.append(widgets.Separator())
        self.append(
            SettingsRow(
                title="Поиск устройств",
                description="Активный поиск новых Bluetooth-устройств поблизости.",
                child=[self.scan_button],
            )
        )
        self.append(widgets.Separator())

        self.append(
            SettingsRow(
                title="Настройки Bluetooth",
                description="Открыть панель Bluetooth в GNOME Settings для расширенной настройки.",
                child=[
                    Button.button(
                        icon="barefoot",
                        label="Открыть",
                        on_click=lambda x: self._open_gnome_settings(),
                    )
                ],
            )
        )

        self.bluetooth_service.connect("notify::powered", self._on_property_changed)
        self.bluetooth_service.connect("device-added", self._on_device_changed)

        asyncio.create_task(self.update_ui())

    def _on_property_changed(self, service, prop):
        asyncio.create_task(self.update_ui())

    def _on_device_changed(self, service, device):
        asyncio.create_task(self.update_ui())

    async def start_scan(self):
        self.scan_button.set_sensitive(False)
        self.scan_button.label = "Поиск..."
        self.scan_button.icon = "bluetooth_searching"

        for child in list(self.device_list_box.child):
            self.device_list_box.remove(child)
        self.device_list_box.append(
            widgets.Label(label="Scanning...", halign="center", vexpand=True)
        )

        self.bluetooth_service.setup_mode = True
        await asyncio.sleep(15)

        self.bluetooth_service.setup_mode = False

        self.scan_button.set_sensitive(True)
        self.scan_button.label = "Поиск устройств"
        self.scan_button.icon = "bluetooth_searching"
        await self.update_ui()

    async def update_ui(self):
        self.powered_switch_row.active = self.bluetooth_service.powered

        for child in list(self.device_list_box.child):
            self.device_list_box.remove(child)

        if self.bluetooth_service.powered:
            found_devices = self.bluetooth_service.devices
            if not found_devices:
                self.device_list_box.append(
                    widgets.Label(
                        label="Устройства не найдены.",
                        halign="center",
                        vexpand=True,
                        css_classes=["no-devices-label"],
                    )
                )
            else:
                for device in found_devices:
                    device_row = self.create_device_row(device)
                    self.device_list_box.append(device_row)
                    device.connect("removed", self._on_device_changed)
        else:
            self.device_list_box.append(
                widgets.Label(label="Bluetooth выключен.", halign="center", vexpand=True)
            )

    def _open_gnome_settings(self):
        try:
            env = os.environ.copy()
            env["XDG_CURRENT_DESKTOP"] = "GNOME"
            subprocess.Popen(["gnome-control-center", "bluetooth"], env=env)
        except FileNotFoundError:
            send_notification("Error", "GNOME Control Center not found.")

    def create_device_row(self, device):
        icon_map = {
            "Headset": "headphones",
            "Audio device": "speaker",
            "Keyboard": "keyboard",
            "Mouse": "mouse",
            "Phone": "phone_android",
            "Camera": "photo_camera",
            "Computer": "computer",
            "Unknown": "bluetooth_connected",
        }

        icon_name = device.icon_name

        mapped_icon = icon_map.get(device.device_type)
        if mapped_icon:
            icon_name = mapped_icon

        row_content = widgets.Box(spacing=10, halign="fill", hexpand=True)

        icon = widgets.Label(
            label=icon_name,
            css_classes=["material-symbols", "icon-label"],
            margin_start=10,
        )
        alias_label = widgets.Label(label=device.alias, hexpand=True, halign="start")

        row_content.append(icon)
        row_content.append(alias_label)

        if device.connected:
            row_content.append(
                widgets.Label(label="Подключено", css_classes=["connected-status-label"])
            )
            button_handler = lambda *_: asyncio.create_task(device.disconnect_from())
        else:
            row_content.append(
                widgets.Label(label="Не подключено", css_classes=["status-label"])
            )
            button_handler = lambda *_: asyncio.create_task(device.connect_to())

        row_button = widgets.Button(
            on_click=button_handler,
            child=row_content,
            css_classes=["network-row"],
        )
        return row_button

    def create_adapter_category(self):
        box = widgets.Box(css_classes=["settings-category"], vertical=True, spacing=0)
        box.append(CategoryLabel("Адаптер Bluetooth"))

        wifi_service = self.bluetooth_service
        self.powered_switch_row = SwitchRow(
            title="Bluetooth",
            description="Включить или выключить адаптер Bluetooth.",
            active=wifi_service.powered,
            on_change=lambda x, active: setattr(wifi_service, "powered", active),
        )
        box.append(self.powered_switch_row)

        return box

    def create_device_category(self):
        box = widgets.Box(css_classes=["settings-category"], vertical=True, spacing=0)
        box.append(CategoryLabel("Устройства"))

        self.device_list_box = widgets.Box(
            vertical=True, spacing=5, css_classes=["network-list-container"]
        )
        box.append(
            SettingsRow(
                title="Сопряжённые и обнаруженные устройства",
                description="Выберите устройство для подключения.",
                vertical=True,
                child=[self.device_list_box],
            )
        )

        return box
