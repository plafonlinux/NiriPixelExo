import time
import json
import os
import subprocess
from ignis import widgets, utils
from ignis.services.notifications import Notification
from ignis.window_manager import WindowManager
from modules.m3components import Button
from gi.repository import Gtk, Gdk


def _resolve_icon(icon: str | None) -> str:
    if not icon:
        return "dialog-information-symbolic"
    if os.path.isabs(icon):
        return icon
    display = Gdk.Display.get_default()
    if display and Gtk.IconTheme.get_for_display(display).has_icon(icon):
        return icon
    return "dialog-information-symbolic"


def relative_time(timestamp: float) -> str:
    diff = int(time.time() - timestamp)

    if diff < 60:
        return "now"
    elif diff < 3600:
        return f"{diff // 60}m"
    elif diff < 86400:
        return f"{diff // 3600}h"
    else:
        return f"{diff // 86400}d"


class ExoNotification(widgets.Box):
    def __init__(self, notification: Notification, compact_popup: bool = False) -> None:
        self._timestamp = notification.time
        self._is_expanded = False

        self._age_label = widgets.Label(
            css_classes=["notification-age"],
            label="",
            halign="start",
            ellipsize="end",
            visible=(not compact_popup),
        )

        self._body_label = (
            widgets.Label(
                css_classes=["notification-body"],
                label=notification.body,
                halign="start",
                ellipsize="end",
                wrap_mode="word_char",
            )
            if notification.body
            else None
        )
        if compact_popup:
            self._body_label.set_single_line_mode(True)

        self._expand_button = (
            Button.button(
                css_classes=["notification-expand"],
                icon="arrow_drop_down",
                valign="start",
                vexpand=False,
                size="xs",
                on_click=self._toggle_expand,
            )
            if self._body_label and not compact_popup
            else None
        )

        self._app_name = notification.app_name
        self._summary = notification.summary
        self._body = notification.body

        _content_button = widgets.Button(
            css_classes=["notification-focus-btn"],
            hexpand=True,
            halign="fill",
            on_click=lambda _: self._focus_app(),
            child=widgets.Box(
                spacing=10,
                child=[
                    widgets.Icon(
                        image=_resolve_icon(notification.icon),
                        pixel_size=24 if not compact_popup else 16,
                        halign="start",
                        valign="start",
                        css_classes=["notification-icon"],
                    ),
                    widgets.Box(
                        css_classes=["notification-info"],
                        vertical=True if not compact_popup else False,
                        valign="center",
                        hexpand=True,
                        halign="fill",
                        spacing=2 if not compact_popup else 8,
                        child=[
                            widgets.Box(
                                spacing=5,
                                child=[
                                    widgets.Label(
                                        css_classes=["notification-summary"],
                                        label=notification.summary,
                                        halign="start",
                                        ellipsize="end",
                                    ),
                                    widgets.Label(
                                        css_classes=["notification-separator"],
                                        label="•",
                                        halign="start",
                                        visible=(not compact_popup),
                                    ),
                                    self._age_label,
                                ],
                            ),
                            self._body_label,
                            widgets.Box(
                                css_classes=["notification-actions-container"],
                                child=[
                                    Button.button(
                                        label=action.label,
                                        on_click=lambda x,
                                        action=action: action.invoke(),
                                        css_classes=["notification-action"],
                                        size="xs",
                                        type="text",
                                    )
                                    for action in notification.actions
                                ],
                            )
                            if notification.actions and not compact_popup
                            else None,
                        ],
                    ),
                ],
            ),
        )

        super().__init__(
            vertical=True,
            hexpand=True,
            halign="fill",
            css_classes=["notification", "compact-popup" if compact_popup else None],
            child=[
                widgets.Box(
                    spacing=4,
                    child=[
                        _content_button,
                        widgets.Box(
                            vertical=True,
                            spacing=5,
                            child=[
                                Button.button(
                                    css_classes=["notification-close"],
                                    icon="close",
                                    valign="start" if not compact_popup else "center",
                                    vexpand=compact_popup,
                                    size="xs",
                                    on_click=lambda x: notification.close(),
                                ),
                                self._expand_button if not compact_popup else None,
                            ],
                        ),
                    ],
                ),
            ],
        )

        self._update_age_label()

        self._poll = utils.Poll(timeout=60_000, callback=self._on_poll)

    def _focus_app(self):
        try:
            combined = f"{self._app_name} {self._summary} {self._body}".lower()
            _SCREENSHOT_KEYWORDS = ("screenshot", "скриншот", "снимок экрана")
            if any(kw in combined for kw in _SCREENSHOT_KEYWORDS):
                WindowManager.get_default().close_window("QuickCenter")
                subprocess.Popen(
                    ["nautilus", os.path.expanduser("~/Pictures/Screenshots")],
                    start_new_session=True,
                )
                return

            result = subprocess.run(
                ["niri", "msg", "--json", "windows"],
                capture_output=True, text=True, timeout=2,
            )
            windows = json.loads(result.stdout)
            name_lower = self._app_name.lower()
            words = [w for w in name_lower.replace("-", " ").split() if len(w) > 2]
            best = None
            for win in windows:
                app_id = win.get("app_id", "").lower()
                if any(w in app_id for w in words) or any(w in name_lower for w in app_id.replace("-", " ").replace(".", " ").split() if len(w) > 2):
                    best = win
                    break
            if best:
                WindowManager.get_default().close_window("QuickCenter")
                subprocess.Popen(["niri", "msg", "action", "focus-window", "--id", str(best["id"])])
        except Exception:
            pass

    def _toggle_expand(self, _):
        self._is_expanded = not self._is_expanded
        if self._body_label:
            self._body_label.set_ellipsize("none" if self._is_expanded else "end")
            self._body_label.set_wrap(self._is_expanded)

        if self._expand_button:
            self._expand_button.set_icon(
                "arrow_drop_up" if self._is_expanded else "arrow_drop_down"
            )

    def _on_poll(self, poll: utils.Poll | None = None):
        """Update the label on each poll tick."""
        self._update_age_label()

        if time.time() - self._timestamp >= 86400 and poll is not None:
            poll.cancel()

    def _update_age_label(self):
        self._age_label.set_label(relative_time(self._timestamp))
