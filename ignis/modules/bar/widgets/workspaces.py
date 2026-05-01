from ignis import widgets, utils
from ignis.services.niri import NiriService, NiriWorkspace, NiriWindow
from ignis.services.applications import ApplicationsService
from user_settings import user_settings
from modules.shared_modules import AppIcon

SERVICE = NiriService.get_default() if NiriService.get_default().is_available else None
APPLICATIONS = ApplicationsService.get_default()

class DummyWorkspace:
    def __init__(self, id: int):
        self.id = id
        self.idx = id

    def switch_to(self):
        if SERVICE:
            SERVICE.switch_to_workspace(self.id)

def get_active_workspace():
    if not SERVICE:
        return None
    for workspace in SERVICE.workspaces:
        if workspace.is_active:
            return workspace
    return None

class WorkspaceButton(widgets.Button):
    def __init__(self, workspace) -> None:
        style = user_settings.interface.modules.options.workspaces_style

        label_text = str(workspace.idx) if isinstance(workspace, NiriWorkspace) else str(workspace.id)

        self.workspace = workspace
        self._label = widgets.Label(label=label_text, halign="center", valign="center")

        children = [self._label]
        self._icons_box = None

        if style == "windows":
            self._icons_box = widgets.Box(spacing=5, css_classes=["workspace-icons"])
            children.append(self._icons_box)

        self._main_content_box = widgets.Box(
            halign="center", valign="center", spacing=4, child=children
        )

        super().__init__(
            css_classes=["workspace"],
            on_click=lambda x: self.workspace.switch_to(),
            child=self._main_content_box,
        )

        def update_css_classes(*args):
            active_workspace = get_active_workspace()
            if active_workspace and self.workspace.id == active_workspace.id:
                self.add_css_class("active")
            else:
                self.remove_css_class("active")
            if not self._get_windows_for_workspace():
                self.add_css_class("empty")
            else:
                self.remove_css_class("empty")

        if SERVICE:
            SERVICE.connect("notify::workspaces", update_css_classes)
            update_css_classes()

        self.update_layout()
        if style == "windows":
            self._update_icons()
            if SERVICE:
                SERVICE.connect("notify::windows", lambda *args: self._update_icons())

    def _get_windows_for_workspace(self):
        if SERVICE:
            return [w for w in SERVICE.windows if w.workspace_id == self.workspace.id]
        return []

    def _update_icons(self):
        if not self._icons_box:
            return

        last_child = self._icons_box.get_last_child()
        while last_child:
            self._icons_box.remove(last_child)
            last_child = self._icons_box.get_last_child()

        windows = self._get_windows_for_workspace()
        self._icons_box.set_visible(bool(windows))

        for window in windows:
            icon_widget = AppIcon(app_id=window.app_id, name=window.title, pixel_size=16)
            self._icons_box.append(icon_widget)

        self._main_content_box.queue_resize()

    def update_layout(self):
        bar = (
            user_settings.interface.bar
            if user_settings.interface.modules.bar_id.workspaces == 0
            else user_settings.interface.bar2
        )
        vertical = bar.vertical
        style = user_settings.interface.modules.options.workspaces_style

        if self._icons_box:
            self._icons_box.set_vertical(vertical)

        if vertical:
            self._main_content_box.set_vertical(True)
            self.set_halign("center")
            self.set_valign("center" if style == "dots" else "fill")
        else:
            self._main_content_box.set_vertical(False)
            self.set_valign("center")
            self.set_halign("center" if style == "dots" else "fill")

        if style == "dots":
            self._main_content_box.set_spacing(0)

class Workspaces(widgets.EventBox):
    def __init__(self):
        self._workspace_box = widgets.Box(
            css_classes=["workspaces"],
            halign="center",
            hexpand=True,
            valign="center",
            vexpand=True,
        )
        user_settings.interface.modules.options.connect_option(
            "workspaces_style", lambda: self.update_workspaces()
        )
        user_settings.interface.modules.options.connect_option(
            "fixed_workspaces_enabled", lambda: self.update_workspaces()
        )
        user_settings.interface.modules.options.connect_option(
            "fixed_workspaces_amount", lambda: self.update_workspaces()
        )

        super().__init__(
            child=[self._workspace_box],
            on_scroll_up=lambda self: self.workspaces_scroll(+1),
            on_scroll_down=lambda self: self.workspaces_scroll(-1),
        )

        self._last_style = None
        self._last_workspace_ids = []
        self._last_fixed_enabled = False

        if SERVICE:
            SERVICE.connect("notify::workspaces", self.update_workspaces)
            self.update_workspaces()
            self.update_layout()

    def update_workspaces(self, *args):
        current_style = user_settings.interface.modules.options.workspaces_style
        current_workspace_ids = [ws.idx for ws in SERVICE.workspaces] if SERVICE else []

        if fixed_enabled := user_settings.interface.modules.options.fixed_workspaces_enabled:
             if fixed_enabled != self._last_fixed_enabled:
                 self._last_style = None
             self._last_workspace_ids = []

        if (current_style != self._last_style or current_workspace_ids != self._last_workspace_ids):
            self._last_style = current_style
            self._last_workspace_ids = current_workspace_ids
            self._last_fixed_enabled = fixed_enabled
            
            fixed_amount = int(user_settings.interface.modules.options.fixed_workspaces_amount)

            self._workspace_box.remove_css_class("dots")
            self._workspace_box.remove_css_class("windows")
            self._workspace_box.remove_css_class("numbers")

            if current_style == "dots":
                self._workspace_box.add_css_class("dots")
            elif current_style == "windows":
                self._workspace_box.add_css_class("windows")
            elif current_style == "numbers":
                self._workspace_box.add_css_class("numbers")

            if SERVICE:
                last_child = self._workspace_box.get_last_child()
                while last_child:
                    self._workspace_box.remove(last_child)
                    last_child = self._workspace_box.get_last_child()

                workspaces_to_display = []
                all_workspaces_map = {ws.idx: ws for ws in SERVICE.workspaces}

                if fixed_enabled and fixed_amount > 0:
                    active_workspace = get_active_workspace()
                    active_workspace_id = active_workspace.idx if active_workspace else None

                    if active_workspace_id is not None:
                        page_base_id = active_workspace_id if fixed_amount == 1 else ((active_workspace_id - 1) // fixed_amount) * fixed_amount + 1
                        for i in range(page_base_id, page_base_id + fixed_amount):
                            workspaces_to_display.append(all_workspaces_map.get(i, DummyWorkspace(i)))
                    else:
                        for i in range(1, fixed_amount + 1):
                            workspaces_to_display.append(all_workspaces_map.get(i, DummyWorkspace(i)))
                else:
                    workspaces_to_display = sorted(list(all_workspaces_map.values()), key=lambda ws: ws.idx)

                for workspace in workspaces_to_display:
                    self._workspace_box.append(WorkspaceButton(workspace))

        elif SERVICE:
            if user_settings.interface.modules.options.fixed_workspaces_enabled:
                self._last_style = None
                self.update_workspaces()
            else:
                for child in self._workspace_box:
                    if isinstance(child, WorkspaceButton) and current_style == "windows":
                        child._update_icons()

    def update_layout(self):
        bar = (
            user_settings.interface.bar
            if user_settings.interface.modules.bar_id.workspaces == 0
            else user_settings.interface.bar2
        )
        vertical = bar.vertical
        spacing = 2 if user_settings.interface.modules.options.workspaces_style == "windows" else 5

        self._workspace_box.set_vertical(vertical)
        self._workspace_box.set_spacing(spacing)

        for child in self._workspace_box:
            if isinstance(child, WorkspaceButton):
                child.update_layout()

    def workspaces_scroll(self, difference: int):
        if not SERVICE:
            return

        active_workspace_niri = next((ws for ws in SERVICE.workspaces if ws.is_active), None)
        if active_workspace_niri:
            SERVICE.switch_to_workspace(active_workspace_niri.idx + difference)

    def widget(self):
        return self
