from warnings import showwarning
from ignis import widgets
from modules.m3components import Button
from scripts import BarStyles, send_notification
from user_settings import user_settings
from ..widgets import (
    CategoryLabel,
    make_toggle_buttons,
    make_independent_toggle_buttons,
    SwitchRow,
    SettingsRow,
)
from ignis.app import IgnisApp

app = IgnisApp.get_initialized()


class BarCategory(widgets.Box):
    def __init__(self):
        bar = user_settings.interface.bar
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
        )

        self.append(CategoryLabel("Панель", "toolbar"))

        self.append(
            SettingsRow(
                title="Расположение",
                description="Выберите сторону для панели.",
                child=[
                    make_toggle_buttons(
                        [
                            ("Верх", "top", "align_vertical_top"),
                            ("Низ", "bottom", "align_vertical_bottom"),
                            ("Лево", "left", "align_horizontal_left"),
                            ("Право", "right", "align_horizontal_right"),
                        ],
                        lambda: bar.side,
                        BarStyles.setSide,
                        on_any_click=None,
                    )
                ],
            )
        )

        self.append(widgets.Separator())

        self.append(
            SettingsRow(
                title="Плотность",
                description="Выберите один из 4 вариантов плотности.",
                child=[
                    make_toggle_buttons(
                        [
                            ("Просторно", 0, "density_large"),
                            ("Комфортно", 1, "density_medium"),
                            ("Компактно", 2, "density_small"),
                            ("Сжато", 3, "list"),
                        ],
                        lambda: bar.density,
                        BarStyles.setCompact,
                        on_any_click=None,
                    )
                ],
            )
        )

        self.append(widgets.Separator())

        self.append(
            SettingsRow(
                title="Модификаторы",
                description="Дополнительные модификаторы панели (можно выбрать несколько).",
                child=[
                    make_independent_toggle_buttons(
                        [
                            (
                                "Плавающая",
                                bar.get_floating,
                                BarStyles.setFloating,
                                "page_header",
                            ),
                            (
                                "Разделённая",
                                bar.get_separation,
                                BarStyles.setSeparation,
                                "more_horiz",
                            ),
                            (
                                "По центру",
                                bar.get_centered,
                                BarStyles.setBarCenter,
                                "code",
                            ),
                        ]
                    )
                ],
            )
        )

        self.append(widgets.Separator())

        self.append(
            SettingsRow(
                title="Фоны",
                description="Добавить или убрать фон панели/модулей.",
                child=[
                    make_independent_toggle_buttons(
                        [
                            (
                                "Панель",
                                bar.get_bar_background,
                                BarStyles.setBarBackground,
                                "toolbar",
                            ),
                            (
                                "Модули",
                                bar.get_module_backgrounds,
                                BarStyles.setModuleBackgrounds,
                                "more_horiz",
                            ),
                        ]
                    )
                ],
            )
        )


class Bar2Category(widgets.Box):
    def __init__(self):
        bar = user_settings.interface.bar2
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
        )

        self.append(CategoryLabel("Вторая панель", "bottom_navigation"))

        self.append(
            SettingsRow(
                description="Вторая панель включается автоматически, если в ней есть модули.\nОна автоматически выключается, когда модулей нет.\nПримечание: отключённые модули во второй панели тоже её активируют.",
            )
        )

        self.append(widgets.Separator())

        self.append(
            SettingsRow(
                title="Расположение",
                description="Выберите сторону для второй панели.",
                child=[
                    make_toggle_buttons(
                        [
                            ("Верх", "top", "align_vertical_top"),
                            ("Низ", "bottom", "align_vertical_bottom"),
                            ("Лево", "left", "align_horizontal_left"),
                            ("Право", "right", "align_horizontal_right"),
                        ],
                        lambda: bar.side,
                        BarStyles.setSide,
                        on_any_click=None,
                        bar_id=1,
                    )
                ],
            )
        )

        self.append(widgets.Separator())

        self.append(
            SettingsRow(
                title="Плотность",
                description="Выберите один из 4 вариантов плотности.",
                child=[
                    make_toggle_buttons(
                        [
                            ("Просторно", 0, "density_large"),
                            ("Комфортно", 1, "density_medium"),
                            ("Компактно", 2, "density_small"),
                            ("Сжато", 3, "list"),
                        ],
                        lambda: bar.density,
                        BarStyles.setCompact,
                        on_any_click=None,
                        bar_id=1,
                    )
                ],
            )
        )

        self.append(widgets.Separator())

        self.append(
            SettingsRow(
                title="Модификаторы",
                description="Дополнительные модификаторы панели (можно выбрать несколько).",
                child=[
                    make_independent_toggle_buttons(
                        [
                            (
                                "Плавающая",
                                bar.get_floating,
                                BarStyles.setFloating,
                                "page_header",
                            ),
                            (
                                "Разделённая",
                                bar.get_separation,
                                BarStyles.setSeparation,
                                "more_horiz",
                            ),
                            (
                                "По центру",
                                bar.get_centered,
                                BarStyles.setBarCenter,
                                "code",
                            ),
                        ],
                        bar_id=1,
                    )
                ],
            )
        )

        self.append(widgets.Separator())

        self.append(
            SettingsRow(
                title="Фоны",
                description="Добавить или убрать фон панели/модулей.",
                child=[
                    make_independent_toggle_buttons(
                        [
                            (
                                "Панель",
                                bar.get_bar_background,
                                BarStyles.setBarBackground,
                                "toolbar",
                            ),
                            (
                                "Модули",
                                bar.get_module_backgrounds,
                                BarStyles.setModuleBackgrounds,
                                "more_horiz",
                            ),
                        ],
                        bar_id=1,
                    )
                ],
            )
        )


class BarModuleSettings(SettingsRow):
    def __init__(self, name: str, widget_name: str, description: str):
        self._widget_name = widget_name

        super().__init__(
            title=f"Виджет «{name}»",
            description=description,
            css_classes=["module-options"],
            child=[
                widgets.Box(
                    vertical=False,
                    child=[
                        make_toggle_buttons(
                            [
                                (None, 0, "timer_1"),
                                (None, 1, "timer_2"),
                            ],
                            lambda: getattr(
                                user_settings.interface.modules.bar_id,
                                self._widget_name,
                            ),
                            self._set_widget_bar_id,
                            on_any_click=None,
                            widget=self._widget_name,
                        ),
                    ],
                ),
                widgets.Separator(),
                widgets.Box(
                    vertical=False,
                    child=[
                        make_toggle_buttons(
                            [
                                ("Начало", 0),
                                ("Центр", 1),
                                ("Конец", 2),
                            ],
                            lambda: getattr(
                                user_settings.interface.modules.location,
                                self._widget_name,
                            ),
                            self._set_widget_location,
                            on_any_click=None,
                            widget=self._widget_name,
                        ),
                    ],
                ),
                widgets.Separator(),
                widgets.Switch(
                    vexpand=False,
                    valign="center",
                    active=getattr(
                        user_settings.interface.modules.visibility,
                        self._widget_name,
                    ),
                    on_change=self._set_widget_visibility,
                ),
            ],
        )

    def _set_widget_location(self, _, value):
        BarStyles.setWidgetLocation(self._widget_name, value)

    def _set_widget_visibility(self, _, active: bool):
        BarStyles.setWidgetVisibility(self._widget_name, active)

    def _set_widget_bar_id(self, _, value):
        BarStyles.setWidgetBarID(self._widget_name, value)


class BarModulesCategory(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("Модули панели", "dashboard_2"),
            ],
        )

        modules = {
            "launcher": {
                "name": "Лаунчер",
                "widget": "launcher",
                "description": "Кнопка для открытия лаунчера.",
            },
            "window_info": {
                "name": "Информация об окне",
                "widget": "window_info",
                "description": "Отображает информацию об активном окне.",
            },
            "media": {
                "name": "Медиа",
                "widget": "media",
                "description": "Показывает текущий медиапроигрыватель с управлением.",
            },
            "workspaces": {
                "name": "Рабочие пространства",
                "widget": "workspaces",
                "description": "Список рабочих пространств.",
            },
            "tasks": {
                "name": "Задачи",
                "widget": "tasks",
                "description": "Закреплённые и запущенные приложения.",
            },
            "recording_indicator": {
                "name": "Индикатор записи",
                "widget": "recording_indicator",
                "description": "Отображает статус записи экрана.",
            },
            "systeminfotray": {
                "name": "Системный трей",
                "widget": "systeminfotray",
                "description": "Иконки системного трея.",
            },
            "clock": {
                "name": "Часы",
                "widget": "clock",
                "description": "Текущее время и дата.",
            },
            "vitals": {
                "name": "Температуры",
                "widget": "vitals",
                "description": "CPU, GPU, SSD температуры и потребление GPU.",
            },
            "updates": {
                "name": "Обновления",
                "widget": "updates",
                "description": "Индикатор доступных обновлений системы.",
            },
            "backup": {
                "name": "Бэкапы",
                "widget": "backup",
                "description": "Статус резервного копирования TimeSync.",
            },
            "apps_btn": {
                "name": "Приложения",
                "widget": "apps_btn",
                "description": "Кнопка запуска ALT Booster — Приложения.",
            },
        }

        for module in modules.values():
            name = module["name"]
            widget_name = module["widget"]
            description = module["description"]

            self.append(BarModuleSettings(name, widget_name, description))
            if module != list(modules.values())[-1]:
                self.append(widgets.Separator())


class ExtraBarCategory(widgets.Box):
    options = user_settings.interface.modules.options

    def __init__(self):
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("Параметры модулей", "settings"),
                SettingsRow(
                    title="Стиль рабочих пространств",
                    description="Выберите один из 3 стилей индикатора рабочих пространств.",
                    child=[
                        make_toggle_buttons(
                            [
                                ("Иконки", "windows", "photo"),
                                ("Цифры", "numbers", "counter_1"),
                                ("Точки", "dots", "more_horiz"),
                            ],
                            lambda: self.options.workspaces_style,
                            BarStyles.setWorkspacesStyle,
                            on_any_click=None,
                        )
                    ],
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Фиксированные пространства",
                    description="Показывать фиксированное количество рабочих пространств.",
                    active=self.options.fixed_workspaces_enabled,
                    on_change=lambda x,
                    active: self.options.set_fixed_workspaces_enabled(active),
                ),
                widgets.Separator(),
                SettingsRow(
                    title="Количество пространств",
                    description="Сколько рабочих пространств отображать.",
                    child=[
                        widgets.SpinButton(
                            min=1,
                            max=20,
                            step=1,
                            value=self.options.fixed_workspaces_amount,
                            on_change=lambda x,
                            value: self.options.set_fixed_workspaces_amount(int(value)),
                        )
                    ],
                ),
                widgets.Separator(),
                SwitchRow(
                    title="24-часовой формат",
                    description="Переключение между 12-часовым (AM/PM) и 24-часовым форматом.",
                    active=self.options.military_time,
                    on_change=lambda x, active: BarStyles.setMilitaryTime(active),
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Показывать дату",
                    description="Включить/выключить отображение даты на панели.",
                    active=self.options.show_date,
                    on_change=lambda x, active: BarStyles.setDateVisibility(active),
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Переставить день и месяц",
                    description="Использовать американский формат даты.",
                    active=self.options.day_month_swapped,
                    on_change=lambda x, active: BarStyles.setDayMonthSwapped(active),
                ),
            ],
        )


class MiscCategory(widgets.Box):
    screen_corners = user_settings.interface.misc.screen_corners

    def __init__(self):
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("Разное", "more_horiz"),
                SwitchRow(
                    title="Скруглённые углы оболочки",
                    description="Добавить закругление снаружи оболочки по краям экрана.",
                    active=user_settings.interface.misc.shell_corners,
                    on_change=lambda x, active: BarStyles.setShellCorners(active),
                ),
                widgets.Separator(),
                SettingsRow(
                    title="Скруглённые углы экрана",
                    description="Скруглить углы экрана.",
                    child=[
                        make_toggle_buttons(
                            [
                                ("Выкл.", "disabled", "close"),
                                (
                                    "Вне полноэкранного",
                                    "not_fullscreen",
                                    "fullscreen_exit",
                                ),
                                ("Всегда", "always", "check"),
                            ],
                            lambda: user_settings.interface.misc.screen_corners,
                            BarStyles.setScreenCorners,
                            on_any_click=None,
                        ),
                    ],
                ),
            ],
        )


class InterfaceTab(widgets.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            spacing=8,
            css_classes=["settings-body"],
            hexpand=False,
            halign="center",
            width_request=800,
        )
        self.append(BarCategory())
        self.append(Bar2Category())
        self.append(BarModulesCategory())
        self.append(ExtraBarCategory())
        self.append(MiscCategory())
        self.hexpand = True
        self.vexpand = True
