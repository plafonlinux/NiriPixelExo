from ignis import widgets
from ignis.services.fetch import FetchService
from ..widgets import CategoryLabel, SettingsRow

fetch = FetchService.get_default()


class SoftwareCategory(widgets.Box):
    def __init__(self):
        if fetch.os_logo:
            self.logo = widgets.Picture(
                image=fetch.os_logo, css_classes=["settings-logo"], height=30
            )

        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("ПО"),
                SettingsRow(
                    title="Операционная система",
                    description=fetch.os_name,
                    vertical=False,
                    child=[self.logo],
                ),
                widgets.Separator(),
                SettingsRow(title="Рабочий стол", description=fetch.current_desktop),
                widgets.Separator(),
                SettingsRow(
                    title="Имя хоста", description=fetch.hostname.replace("\n", "")
                ),
            ],
        )


class AppearanceCategory(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("Внешний вид"),
                SettingsRow(title="GTK-тема", description=fetch.gtk_theme),
                widgets.Separator(),
                SettingsRow(title="Тема иконок", description=fetch.icon_theme),
            ],
        )


class HardwareCategory(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("Железо"),
                SettingsRow(title="Процессор", description=fetch.cpu),
                widgets.Separator(),
                SettingsRow(
                    title="ОЗУ",
                    description=(str(round(fetch.mem_total / 1024 / 1024, 2)) + " GiB"),
                ),
            ],
        )


class AboutTab(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["settings-body"],
            vertical=True,
            spacing=8,
            hexpand=False,
            halign="center",
            width_request=800,
            child=[SoftwareCategory(), AppearanceCategory(), HardwareCategory()],
        )
