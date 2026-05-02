import subprocess
from ignis import widgets


class QuickMenuButton:
    def __init__(self):
        self._button = widgets.Button(
            child=widgets.Label(
                label="menu",
                css_classes=["quick-menu-icon"],
            ),
            css_classes=["quick-menu-btn"],
            tooltip_text="Быстрое меню",
            on_click=lambda _: subprocess.Popen(
                ["ignis", "open-window", "QuickCenter"], start_new_session=True
            ),
        )

    def widget(self):
        return self._button
