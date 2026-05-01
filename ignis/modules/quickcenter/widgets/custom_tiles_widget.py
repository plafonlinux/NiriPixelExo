import subprocess
from ignis import widgets
from modules.shared_modules.custom_tiles_store import get_tiles, connect_changed


class _CustomTile(widgets.Button):
    def __init__(self, tile: dict):
        super().__init__(
            css_classes=["quick-tile", "button"],
            hexpand=True,
            tooltip_text=tile["command"],
            child=widgets.Box(
                spacing=8,
                child=[
                    widgets.Label(
                        label=tile["icon"],
                        css_classes=["qt-icon", "m3-icon"],
                    ),
                    widgets.Label(
                        label=tile["label"],
                        css_classes=["qt-title"],
                        halign="start",
                        hexpand=True,
                        ellipsize="end",
                    ),
                ],
            ),
            on_click=lambda _, cmd=tile["command"]: subprocess.Popen(
                cmd, shell=True, start_new_session=True
            ),
        )


class CustomTilesWidget(widgets.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            hexpand=True,
            spacing=8,
            visible=False,
        )
        self._rebuild()
        connect_changed(self._rebuild)

    def _rebuild(self):
        for child in list(self.child):
            self.remove(child)

        tiles = get_tiles()
        self.set_visible(bool(tiles))

        for i in range(0, len(tiles), 2):
            row = widgets.Box(
                css_classes=["quick-tiles-row"],
                hexpand=True,
                spacing=8,
            )
            row.append(_CustomTile(tiles[i]))
            if i + 1 < len(tiles):
                row.append(_CustomTile(tiles[i + 1]))
            self.append(row)
