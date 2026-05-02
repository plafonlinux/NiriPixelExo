from ignis import widgets
from modules.m3components import Button
from modules.settings.widgets import CategoryLabel, SettingsRow, SwitchRow
from modules.shared_modules.custom_tiles_store import (
    get_tiles, add_tile, remove_tile, connect_changed,
)
from user_settings import user_settings


# ── QuickToggles tiles ────────────────────────────────────────────────────────

class QuickTogglesTilesCategory(widgets.Box):
    def __init__(self):
        qt = user_settings.interface.quicktoggles
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("Плитки Quick Меню", "grid_view"),
                SwitchRow(
                    title="Wi-Fi",
                    description="Показывать плитку управления Wi-Fi.",
                    active=qt.show_wifi,
                    on_change=lambda x, active: qt.set_show_wifi(active),
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Bluetooth",
                    description="Показывать плитку управления Bluetooth.",
                    active=qt.show_bluetooth,
                    on_change=lambda x, active: qt.set_show_bluetooth(active),
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Тюнер",
                    description="Показывать плитку Тюнера.",
                    active=qt.show_tuner,
                    on_change=lambda x, active: qt.set_show_tuner(active),
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Настройки GNOME",
                    active=qt.show_gnome_settings,
                    on_change=lambda x, active: qt.set_show_gnome_settings(active),
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Thunderbird",
                    active=qt.show_thunderbird,
                    on_change=lambda x, active: qt.set_show_thunderbird(active),
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Bitwarden",
                    active=qt.show_bitwarden,
                    on_change=lambda x, active: qt.set_show_bitwarden(active),
                ),
            ],
        )


# ── Custom tiles ──────────────────────────────────────────────────────────────

class _TileRow(widgets.Box):
    def __init__(self, index: int, tile: dict, on_delete):
        subtitle = tile.get("subtitle", "")

        title_box_children = [
            widgets.Label(
                label=tile["label"],
                css_classes=["ct-row-label"],
                halign="start",
                hexpand=True,
                ellipsize=3,
            ),
        ]
        if subtitle:
            title_box_children.append(
                widgets.Label(
                    label=subtitle,
                    css_classes=["ct-row-subtitle"],
                    halign="start",
                    hexpand=True,
                    ellipsize=3,
                )
            )
        title_box_children.append(
            widgets.Label(
                label=tile["command"],
                css_classes=["ct-row-cmd"],
                halign="start",
                hexpand=True,
                ellipsize=3,
            )
        )

        super().__init__(
            css_classes=["settings-row", "ct-tile-row"],
            hexpand=True,
            halign="fill",
            spacing=12,
            child=[
                widgets.Label(
                    label=tile["icon"],
                    css_classes=["m3-icon", "ct-row-icon"],
                ),
                widgets.Box(
                    vertical=True,
                    hexpand=True,
                    spacing=2,
                    child=title_box_children,
                ),
                Button.button(
                    icon="delete",
                    size="xs",
                    type="text",
                    on_click=lambda _, i=index: on_delete(i),
                    tooltip_text="Удалить",
                    valign="center",
                    halign="end",
                ),
            ],
        )


class _AddForm(widgets.Box):
    def __init__(self, on_add):
        self._icon_entry = widgets.Entry(
            placeholder_text="Иконка (bolt, wifi…)",
            hexpand=True,
            css_classes=["ct-entry"],
        )
        self._label_entry = widgets.Entry(
            placeholder_text="Название",
            hexpand=True,
            css_classes=["ct-entry"],
        )
        self._subtitle_entry = widgets.Entry(
            placeholder_text="Описание (необязательно)",
            hexpand=True,
            css_classes=["ct-entry"],
        )
        self._cmd_entry = widgets.Entry(
            placeholder_text="Команда (kitty, code…)",
            hexpand=True,
            css_classes=["ct-entry"],
            on_accept=lambda _: self._submit(on_add),
        )

        self._icon_preview = widgets.Label(
            label="add_box",
            css_classes=["m3-icon", "ct-icon-preview"],
        )
        self._icon_entry.connect(
            "notify::text",
            lambda e, _: self._icon_preview.set_label(e.get_text() or "add_box"),
        )

        super().__init__(
            css_classes=["settings-row", "ct-add-form"],
            vertical=True,
            hexpand=True,
            halign="fill",
            spacing=8,
            child=[
                widgets.Box(
                    spacing=8,
                    child=[self._icon_preview, self._icon_entry],
                ),
                self._label_entry,
                self._subtitle_entry,
                self._cmd_entry,
                widgets.Box(
                    halign="end",
                    child=[
                        Button.button(
                            icon="add",
                            label="Добавить",
                            size="xs",
                            on_click=lambda _: self._submit(on_add),
                            halign="end",
                            valign="center",
                        )
                    ],
                ),
            ],
        )

    def _submit(self, on_add):
        icon = self._icon_entry.get_text().strip()
        label = self._label_entry.get_text().strip()
        subtitle = self._subtitle_entry.get_text().strip()
        cmd = self._cmd_entry.get_text().strip()
        if icon and label and cmd:
            on_add(icon, label, cmd, subtitle)
            self._icon_entry.set_text("")
            self._label_entry.set_text("")
            self._subtitle_entry.set_text("")
            self._cmd_entry.set_text("")
            self._icon_preview.set_label("add_box")


class _CustomTilesCategory(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
        )
        self._list_box = widgets.Box(vertical=True, spacing=0)
        self.append(CategoryLabel("Кастомные кнопки", "add_circle"))
        self.append(self._list_box)
        self._rebuild_list()
        connect_changed(self._rebuild_list)

        self.append(widgets.Separator())
        self.append(
            SettingsRow(
                title="Добавить кнопку",
                description="Иконка — название из Material Symbols.",
            )
        )
        self.append(widgets.Separator())
        self.append(_AddForm(self._on_add))

    def _rebuild_list(self):
        for child in list(self._list_box.child):
            self._list_box.remove(child)

        tiles = get_tiles()
        if not tiles:
            self._list_box.append(
                widgets.Label(
                    label="Нет кастомных кнопок",
                    css_classes=["ct-empty-label"],
                    halign="center",
                    margin_top=16,
                    margin_bottom=16,
                )
            )
        else:
            for i, tile in enumerate(tiles):
                if i > 0:
                    self._list_box.append(widgets.Separator())
                self._list_box.append(_TileRow(i, tile, self._on_delete))

    def _on_add(self, icon: str, label: str, command: str, subtitle: str = ""):
        add_tile(icon, label, command, subtitle)

    def _on_delete(self, index: int):
        remove_tile(index)


# ── Tab ───────────────────────────────────────────────────────────────────────

class QuickMenuTab(widgets.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            spacing=8,
            css_classes=["settings-body"],
            hexpand=False,
            halign="center",
            width_request=800,
        )
        self.append(QuickTogglesTilesCategory())
        self.append(_CustomTilesCategory())
