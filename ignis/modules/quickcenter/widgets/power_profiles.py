import subprocess
import asyncio
from ignis import widgets, utils


PROFILES = [
    ("performance", "bolt", "Перф."),
    ("balanced", "balance", "Баланс"),
    ("power-saver", "energy_savings_leaf", "Эко"),
]


def _get_current_profile() -> str:
    try:
        return subprocess.check_output(
            ["powerprofilesctl", "get"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "balanced"


class PowerProfilesWidget(widgets.Box):
    def __init__(self):
        self._buttons: dict[str, widgets.Button] = {}
        children = []

        for profile, icon, label in PROFILES:
            btn = widgets.Button(
                css_classes=["quick-toggle", "m3-button"],
                hexpand=True,
                child=widgets.Box(
                    vertical=True,
                    spacing=2,
                    halign="center",
                    valign="center",
                    child=[
                        widgets.Label(label=icon, css_classes=["quick-toggle-icon"]),
                        widgets.Label(label=label),
                    ],
                ),
                on_click=lambda _, p=profile: self._set_profile(p),
            )
            self._buttons[profile] = btn
            children.append(btn)

        super().__init__(
            css_classes=["quick-toggles-container"],
            hexpand=True,
            halign="fill",
            spacing=2,
            child=children,
        )

        self._mark_active(_get_current_profile())

    def _mark_active(self, profile: str):
        for p, btn in self._buttons.items():
            classes = list(btn.get_css_classes())
            if p == profile:
                if "active" not in classes:
                    classes.append("active")
            elif "active" in classes:
                classes.remove("active")
            btn.set_css_classes(classes)

    def _set_profile(self, profile: str):
        self._mark_active(profile)
        asyncio.create_task(utils.exec_sh_async(f"powerprofilesctl set {profile}"))
