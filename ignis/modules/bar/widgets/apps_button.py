import subprocess
from ignis import widgets


class AppsButton:
    def __init__(self):
        self._button = widgets.Button(
            child=widgets.Box(
                spacing=4,
                child=[
                    widgets.Label(
                        label="apps",
                        css_classes=["apps-btn-icon"],
                    ),
                    widgets.Label(
                        label="Приложения",
                        css_classes=["apps-btn-text"],
                    ),
                ],
            ),
            css_classes=["apps-btn"],
            tooltip_text="ALT Booster — Приложения",
            on_click=lambda _: subprocess.Popen(
                ["altbooster", "-a"], start_new_session=True
            ),
        )

    def widget(self):
        return self._button
