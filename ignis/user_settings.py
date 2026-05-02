import os
from ignis import utils
from ignis.app import IgnisApp
from ignis.options_manager import OptionsGroup, OptionsManager, TrackedList
from ignis.window_manager import WindowManager

window_manager = WindowManager.get_default()
app = IgnisApp.get_initialized()


class UserSettings(OptionsManager):
    def __init__(self):
        super().__init__(file=os.path.expanduser("~/.config/ignis/user_settings.json"))

    class Appearance(OptionsGroup):
        class WallpaperColors(OptionsGroup):
            # Wallpaper / Colours
            quickselect_path: str = ""
            wallpaper_path: str = ""
            color_scheme: str = "neutral"
            dark_mode: bool = True

            class AutoDark(OptionsGroup):
                enabled: bool = False
                start_hour: int = 22
                start_min: int = 0
                end_hour: int = 6
                end_min: int = 0

            auto_dark = AutoDark()

        wallcolors = WallpaperColors()

    class Interface(OptionsGroup):
        class Modules(OptionsGroup):
            class Locations(OptionsGroup):
                launcher: int = 0
                window_info: int = 0
                media: int = 1
                workspaces: int = 0
                tasks: int = 0
                recording_indicator: int = 2
                systeminfotray: int = 2
                clock: int = 1
                vitals: int = 2
                keyboard_layout: int = 2

            class Visibility(OptionsGroup):
                window_info: bool = False
                media: bool = True
                workspaces: bool = True
                recording_indicator: bool = True
                systeminfotray: bool = True
                clock: bool = True
                tasks: bool = True
                launcher: bool = False
                vitals: bool = True
                power_profile: bool = True
                lavd: bool = True
                localsend: bool = True
                keyboard_layout: bool = True

            class BarID(OptionsGroup):
                launcher: int = 0
                window_info: int = 0
                media: int = 0
                workspaces: int = 0
                tasks: int = 0
                recording_indicator: int = 0
                systeminfotray: int = 0
                clock: int = 0
                vitals: int = 0
                keyboard_layout: int = 0

            class ModuleOptions(OptionsGroup):
                show_date: bool = True
                day_month_swapped: bool = False
                military_time: bool = True
                recording_indicator: str = "recording"
                workspaces_style: str = "dots"
                fixed_workspaces_enabled: bool = False
                fixed_workspaces_amount: int = 5

            location = Locations()
            visibility = Visibility()
            bar_id = BarID()
            options = ModuleOptions()

        class Bar(OptionsGroup):
            side: str = "top"
            vertical: bool = False
            density: int = 3
            floating: bool = True
            separation: bool = True
            centered: bool = False
            bar_background: bool = True
            module_backgrounds: bool = False

        class Bar2(OptionsGroup):
            enabled: bool = False
            side: str = "top"
            vertical: bool = False
            density: int = 3
            floating: bool = True
            separation: bool = False
            centered: bool = False
            bar_background: bool = True
            module_backgrounds: bool = True

        class Notifications(OptionsGroup):
            anchor: list = ["top"]
            compact_popup: bool = True

        class Launcher(OptionsGroup):
            layout: str = "grid"

        class Misc(OptionsGroup):
            shell_corners: bool = True
            screen_corners: str = "disabled"

        modules = Modules()
        bar = Bar()
        bar2 = Bar2()
        notifications = Notifications()
        launcher = Launcher()
        misc = Misc()

    class Services(OptionsGroup):
        class Recorder(OptionsGroup):
            start_notification: bool = False
            stop_notification: bool = False
            record_audio: bool = True

        class OSD(OptionsGroup):
            anchor: list = ["bottom"]
            vertical: bool = False

        recorder = Recorder()
        osd = OSD()

    appearance = Appearance()
    interface = Interface()
    services = Services()


user_settings = UserSettings()
