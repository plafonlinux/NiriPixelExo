from ignis import widgets
from modules.m3components.button import Button
from user_settings import user_settings
from ..widgets import (
    CategoryLabel,
    SettingsRow,
    SwitchRow,
    make_toggle_buttons,
    make_independent_toggle_buttons,
)
from scripts import BarStyles, send_notification
from ignis.options import options


class NotificationsCategory(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("Уведомления", "notifications"),
                SwitchRow(
                    title="Не беспокоить",
                    description="Блокирует всплывающие уведомления.",
                    active=options.notifications.dnd,
                    on_change=lambda x, active: options.notifications.set_dnd(active),
                ),
                widgets.Separator(),
                SettingsRow(
                    title="Время показа",
                    description="Сколько секунд отображается всплывающее уведомление.",
                    child=[
                        widgets.SpinButton(
                            min=1,
                            max=60,
                            step=1,
                            value=(options.notifications.popup_timeout / 1000),
                            on_change=lambda _,
                            value: options.notifications.set_popup_timeout(
                                value * 1000
                            ),
                        )
                    ],
                ),
                widgets.Separator(),
                SettingsRow(
                    title="Макс. уведомлений",
                    description="Сколько уведомлений показывать одновременно.",
                    child=[
                        widgets.SpinButton(
                            min=1,
                            max=20,
                            step=1,
                            value=options.notifications.max_popups_count,
                            on_change=lambda _,
                            value: options.notifications.set_max_popups_count(value),
                        )
                    ],
                ),
                widgets.Separator(),
                SettingsRow(
                    title="Расположение",
                    description="Выберите место для всплывающих уведомлений.",
                    child=[
                        make_toggle_buttons(
                            [
                                ("", ["top", "left"], "north_west"),
                                ("Верх", ["top"], "north"),
                                ("", ["top", "right"], "north_east"),
                                ("", ["bottom", "left"], "south_west"),
                                ("Низ", ["bottom"], "south"),
                                ("", ["bottom", "right"], "south_east"),
                            ],
                            lambda: user_settings.interface.notifications.anchor,
                            user_settings.interface.notifications.set_anchor,
                            on_any_click=None,
                        ),
                    ],
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Компактный поп-ап",
                    description="Показывать более компактное всплывающее уведомление.",
                    active=user_settings.interface.notifications.compact_popup,
                    on_change=lambda x,
                    active: user_settings.interface.notifications.set_compact_popup(
                        active
                    ),
                ),
                widgets.Separator(),
                SettingsRow(
                    title="Тестовое уведомление",
                    child=[
                        Button.button(
                            icon="notifications_unread",
                            label="Отправить тест",
                            halign="start",
                            size="xs",
                            on_click=lambda x: send_notification(
                                "Тестовое уведомление", "Это тестовое уведомление!"
                            ),
                        )
                    ],
                ),
            ],
        )


class RecordingCategory(widgets.Box):
    def __init__(self):
        self.recorder = user_settings.services.recorder

        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("Запись экрана", "screen_record"),
                SettingsRow(
                    title="Уведомления",
                    description="Когда рекордер должен отправлять уведомление.",
                    child=[
                        make_independent_toggle_buttons(
                            [
                                (
                                    "Старт",
                                    self.recorder.get_start_notification,
                                    self.recorder.set_start_notification,
                                    "play_arrow",
                                ),
                                (
                                    "Стоп",
                                    self.recorder.get_stop_notification,
                                    self.recorder.set_stop_notification,
                                    "stop",
                                ),
                            ]
                        )
                    ],
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Записывать аудио",
                    description="Записывать системный звук при захвате экрана.",
                    active=self.recorder.record_audio,
                    on_change=lambda x, active: self.recorder.set_record_audio(active),
                ),
                widgets.Separator(),
                SettingsRow(
                    title="Индикатор записи",
                    description="Когда показывать индикатор записи на панели.",
                    child=[
                        make_toggle_buttons(
                            [
                                ("Всегда", "always", "visibility"),
                                ("При записи", "recording", "screen_record"),
                            ],
                            lambda: user_settings.interface.modules.options.recording_indicator,
                            BarStyles.setRecordingIndicator,
                            on_any_click=None,
                        ),
                    ],
                ),
            ],
        )


class OSDCategory(widgets.Box):
    def __init__(self):
        self.recorder = user_settings.services.recorder

        super().__init__(
            css_classes=["settings-category"],
            vertical=True,
            spacing=0,
            child=[
                CategoryLabel("OSD", "toast"),
                SettingsRow(
                    title="Расположение OSD",
                    description="Выберите позицию для OSD-попапов.",
                    child=[
                        make_toggle_buttons(
                            [
                                ("", ["top", "left"], "north_west"),
                                ("Верх", ["top"], "north"),
                                ("", ["top", "right"], "north_east"),
                                ("", ["left"], "west"),
                                ("", ["right"], "east"),
                                ("", ["bottom", "left"], "south_west"),
                                ("Низ", ["bottom"], "south"),
                                ("", ["bottom", "right"], "south_east"),
                            ],
                            lambda: user_settings.services.osd.anchor,
                            user_settings.services.osd.set_anchor,
                            on_any_click=None,
                        ),
                    ],
                ),
                widgets.Separator(),
                SwitchRow(
                    title="Вертикальный",
                    description="Вертикальный OSD. Действует только при угловом расположении.",
                    active=user_settings.services.osd.vertical,
                    on_change=lambda x, active: user_settings.services.osd.set_vertical(
                        active
                    ),
                ),
            ],
        )


class ServicesTab(widgets.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            spacing=8,
            css_classes=["settings-body"],
            hexpand=False,
            halign="center",
            width_request=800,
        )
        self.append(NotificationsCategory())
        self.append(RecordingCategory())
        self.append(OSDCategory())
