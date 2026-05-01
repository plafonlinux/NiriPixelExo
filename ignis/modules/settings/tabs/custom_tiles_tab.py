from ignis import widgets
from modules.m3components import Button
from modules.settings.widgets import CategoryLabel, SettingsRow
from modules.shared_modules.custom_tiles_store import (
    get_tiles, add_tile, remove_tile, connect_changed, disconnect_changed,
)


class _TileRow(widgets.Box):
    def __init__(self, index: int, tile: dict, on_delete):
        icon_preview = widgets.Label(
            label=tile["icon"],
            css_classes=["m3-icon", "ct-row-icon"],
        )
        label_text = widgets.Label(
            label=tile["label"],
            css_classes=["ct-row-label"],
            halign="start",
            hexpand=True,
            ellipsize=3,
        )
        cmd_text = widgets.Label(
            label=tile["command"],
            css_classes=["ct-row-cmd"],
            halign="start",
            hexpand=True,
            ellipsize=3,
        )

        delete_btn = Button.button(
            icon="delete",
            size="xs",
            type="text",
            on_click=lambda _, i=index: on_delete(i),
            tooltip_text="Удалить",
            valign="center",
            halign="end",
        )

        super().__init__(
            css_classes=["settings-row", "ct-tile-row"],
            hexpand=True,
            halign="fill",
            spacing=12,
            child=[
                icon_preview,
                widgets.Box(
                    vertical=True,
                    hexpand=True,
                    spacing=2,
                    child=[label_text, cmd_text],
                ),
                delete_btn,
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

        add_btn = Button.button(
            icon="add",
            label="Добавить",
            size="xs",
            on_click=lambda _: self._submit(on_add),
            halign="end",
            valign="center",
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
                    child=[
                        self._icon_preview,
                        self._icon_entry,
                    ],
                ),
                self._label_entry,
                self._cmd_entry,
                widgets.Box(halign="end", child=[add_btn]),
            ],
        )

    def _submit(self, on_add):
        icon = self._icon_entry.get_text().strip()
        label = self._label_entry.get_text().strip()
        cmd = self._cmd_entry.get_text().strip()
        if icon and label and cmd:
            on_add(icon, label, cmd)
            self._icon_entry.set_text("")
            self._label_entry.set_text("")
            self._cmd_entry.set_text("")
            self._icon_preview.set_label("add_box")


class CustomTilesTab(widgets.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            spacing=8,
            css_classes=["settings-body"],
            hexpand=False,
            halign="center",
            width_request=800,
        )
        self._list_box = None
        self._rebuild()
        connect_changed(self._rebuild)

    def _rebuild(self):
        for child in list(self.child):
            self.remove(child)

        tiles = get_tiles()

        # ── List ──────────────────────────────────────────────────
        list_category = widgets.Box(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
        )
        list_category.append(CategoryLabel("Кастомные кнопки", "grid_view"))

        if not tiles:
            list_category.append(
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
                    list_category.append(widgets.Separator())
                list_category.append(_TileRow(i, tile, self._on_delete))

        self.append(list_category)

        # ── Add form ──────────────────────────────────────────────
        form_category = widgets.Box(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
        )
        form_category.append(CategoryLabel("Добавить кнопку", "add_circle"))
        form_category.append(
            SettingsRow(
                description="Введи иконку (Material Symbol), название и команду.",
            )
        )
        form_category.append(widgets.Separator())
        form_category.append(_AddForm(self._on_add))

        self.append(form_category)

    def _on_add(self, icon: str, label: str, command: str):
        add_tile(icon, label, command)

    def _on_delete(self, index: int):
        remove_tile(index)
