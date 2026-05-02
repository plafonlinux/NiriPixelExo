from ignis.css_manager import CssManager
from ignis.window_manager import WindowManager
from scripts import BarStyles
from scripts.recorder import set_indicator
from user_settings import user_settings

from ignis import widgets

from .widgets import (
    Clock,
    KeyboardLayout,
    LAVDToggle,
    Launcher,
    Media,
    PowerProfileIndicator,
    QuickLaunch,
    SystemInfoTray,
    Tasks,
    Vitals,
    WindowInfo,
    Workspaces,
    UpdatesIndicator,
    BackupIndicator,
    AppsButton,
    QuickMenuButton,
)
from .widgets.recording_indicator import RecordingIndicator

css_manager = CssManager.get_default()
window_manager = WindowManager.get_default()


class Bar:
    def __init__(self, monitor: int = 0):
        self.monitor = monitor
        self.__wins = {}
        self.media = Media()
        self.window_info = WindowInfo()
        self.workspaces = Workspaces()
        self.recording_indicator = RecordingIndicator()
        self.clock = Clock()
        self.tasks = Tasks()
        self.launcher = Launcher()
        self.quicklaunch = QuickLaunch()
        self.vitals = Vitals()
        self.updates = UpdatesIndicator()
        self.backup = BackupIndicator()
        self.apps_btn = AppsButton()
        self.quick_menu = QuickMenuButton()
        self.power_profile_indicator = PowerProfileIndicator()
        self.lavd_toggle = LAVDToggle()
        self.systeminfotray = SystemInfoTray()
        self.keyboard_layout = KeyboardLayout()
        set_indicator(self.recording_indicator)

        self.left_widgets = None
        self.center_widgets = None
        self.right_widgets = None
        self.left_widgets2 = None
        self.center_widgets2 = None
        self.right_widgets2 = None

        self.media_widget = self.media.widget()
        self.window_info_widget = self.window_info.widget()
        self.workspaces_widget = self.workspaces.widget()
        self.recording_indicator_widget = self.recording_indicator.widget()
        self.systeminfotray_widget = self.systeminfotray.widget()
        self.clock_widget = self.clock.widget()
        self.tasks_widget = self.tasks.widget()
        self.launcher_widget = self.launcher.widget()
        self.quicklaunch_widget = self.quicklaunch.widget()
        self.vitals_widget = self.vitals.widget()
        self.updates_widget = self.updates.widget()
        self.backup_widget = self.backup.widget()
        self.apps_btn_widget = self.apps_btn.widget()
        self.quick_menu_widget = self.quick_menu.widget()
        self.power_profile_widget = self.power_profile_indicator.widget()
        self.lavd_widget = self.lavd_toggle.widget()
        self.keyboard_layout_widget = self.keyboard_layout.widget()

    def build(self):
        side = user_settings.interface.bar.side
        vertical = user_settings.interface.bar.vertical
        compact_mode = user_settings.interface.bar.density

        height = 40
        width = 40
        if compact_mode == 1:
            height = 35
            width = 35
        elif compact_mode == 2:
            height = 30
            width = 30
        elif compact_mode == 3:
            height = 25
            width = 25

        anchors = (
            [side]
            if user_settings.interface.bar.centered
            else (["top", "bottom", side] if vertical else ["left", "right", side])
        )

        if vertical:
            size_request = {"width_request": width}
        else:
            size_request = {"height_request": height}

        self.left_widgets = widgets.Box(
            vertical=vertical,
            spacing=2,
            css_classes=["left-widgets"],
        )

        self.center_widgets = widgets.Box(
            vertical=vertical,
            spacing=2,
            css_classes=["center-widgets"],
        )

        self.right_widgets = widgets.Box(
            vertical=vertical,
            spacing=2,
            css_classes=["right-widgets"],
        )

        self.__wins[0] = widgets.Window(
            namespace="Bar" + str(self.monitor),
            monitor=self.monitor,
            anchor=anchors,
            css_classes=["bar"],
            exclusivity="exclusive",
            **size_request,
            child=widgets.CenterBox(
                vertical=vertical,
                css_classes=["bar-widgets"],
                start_widget=self.left_widgets,
                center_widget=self.center_widgets,
                end_widget=self.right_widgets,
            ),
        )

        return self.__wins[0]

    def build2(self):
        side = user_settings.interface.bar2.side
        vertical = user_settings.interface.bar2.vertical
        compact_mode = user_settings.interface.bar2.density

        height = 40
        width = 40
        if compact_mode == 1:
            height = 35
            width = 35
        elif compact_mode == 2:
            height = 30
            width = 30
        elif compact_mode == 3:
            height = 25
            width = 25

        anchors = (
            [side]
            if user_settings.interface.bar2.centered
            else (["top", "bottom", side] if vertical else ["left", "right", side])
        )

        if vertical:
            size_request = {"width_request": width}
        else:
            size_request = {"height_request": height}

        self.left_widgets2 = widgets.Box(
            vertical=vertical,
            spacing=2,
            css_classes=["left-widgets"],
        )

        self.center_widgets2 = widgets.Box(
            vertical=vertical,
            spacing=2,
            css_classes=["center-widgets"],
        )

        self.right_widgets2 = widgets.Box(
            vertical=vertical,
            spacing=2,
            css_classes=["right-widgets"],
        )

        self.__wins[1] = widgets.Window(
            namespace="Bar2" + str(self.monitor),
            monitor=self.monitor,
            anchor=anchors,
            css_classes=["bar"],
            exclusivity="exclusive",
            visible=user_settings.interface.bar2.enabled,
            **size_request,
            child=widgets.CenterBox(
                vertical=vertical,
                css_classes=["bar-widgets"],
                start_widget=self.left_widgets2,
                center_widget=self.center_widgets2,
                end_widget=self.right_widgets2,
            ),
        )

        self.update_layout()

        return self.__wins[1]

    def update_layout(self):
        for area in [
            self.left_widgets,
            self.center_widgets,
            self.right_widgets,
            self.left_widgets2,
            self.center_widgets2,
            self.right_widgets2,
        ]:
            area.set_child([])

        location_setting = user_settings.interface.modules.location
        visibility_setting = user_settings.interface.modules.visibility
        bar_id_setting = user_settings.interface.modules.bar_id

        widgets = {
            "launcher": {
                "name": "launcher",
                "widget": self.launcher_widget,
            },
            "window_info": {
                "name": "window_info",
                "widget": self.window_info_widget,
            },
            "workspaces": {
                "name": "workspaces",
                "widget": self.workspaces_widget,
            },
            "tasks": {
                "name": "tasks",
                "widget": self.tasks_widget,
            },
            "media": {
                "name": "media",
                "widget": self.media_widget,
            },
            "clock": {
                "name": "clock",
                "widget": self.clock_widget,
            },
            "recording_indicator": {
                "name": "recording_indicator",
                "widget": self.recording_indicator_widget,
            },
            "vitals": {
                "name": "vitals",
                "widget": self.vitals_widget,
            },
            "updates": {
                "name": "updates",
                "widget": self.updates_widget,
            },
            "backup": {
                "name": "backup",
                "widget": self.backup_widget,
            },
            "apps_btn": {
                "name": "apps_btn",
                "widget": self.apps_btn_widget,
            },
            "power_profile": {
                "name": "power_profile",
                "widget": self.power_profile_widget,
            },
            "lavd": {
                "name": "lavd",
                "widget": self.lavd_widget,
            },
            "keyboard_layout": {
                "name": "keyboard_layout",
                "widget": self.keyboard_layout_widget,
            },
            "systeminfotray": {
                "name": "systeminfotray",
                "widget": self.systeminfotray_widget,
            },
            "quick_menu": {
                "name": "quick_menu",
                "widget": self.quick_menu_widget,
            },
        }

        def location(location, bar_id):
            if bar_id == 0:
                if location == 0:
                    return self.left_widgets
                elif location == 1:
                    return self.center_widgets
                elif location == 2:
                    return self.right_widgets
                else:
                    raise ValueError("Invalid location")
            elif bar_id == 1:
                if location == 0:
                    return self.left_widgets2
                elif location == 1:
                    return self.center_widgets2
                elif location == 2:
                    return self.right_widgets2
                else:
                    raise ValueError("Invalid location")
            else:
                raise ValueError("Invalid bar id")

        for widget in widgets.values():
            if widget["name"] in ("vitals", "power_profile", "lavd"):
                # These always follow systeminfotray's position
                a = getattr(location_setting, "systeminfotray")
                b = getattr(bar_id_setting, "systeminfotray")
            else:
                a = getattr(location_setting, widget["name"])
                b = getattr(bar_id_setting, widget["name"])

            location(a, b).append(widget["widget"])
            widget["widget"].set_visible(getattr(visibility_setting, widget["name"]))

        # QuickLaunch is a standalone bubble in center, same bar as tasks
        tasks_bar = getattr(bar_id_setting, "tasks")
        center = self.center_widgets if tasks_bar == 0 else self.center_widgets2
        center.append(self.quicklaunch_widget)

        for area in [
            self.left_widgets,
            self.center_widgets,
            self.right_widgets,
            self.left_widgets2,
            self.center_widgets2,
            self.right_widgets2,
        ]:
            if len(area.child) == 0:
                area.add_css_class("empty")
            else:
                area.remove_css_class("empty")

        if (
            len(self.left_widgets2.child) == 0
            and len(self.center_widgets2.child) == 0
            and len(self.right_widgets2.child) == 0
        ):
            user_settings.interface.bar2.set_enabled(False)
            self.__wins[1].set_visible(False)
        else:
            user_settings.interface.bar2.set_enabled(True)
            self.__wins[1].set_visible(True)

    def get_window(self, bar_id: int):
        return self.__wins.get(bar_id)
