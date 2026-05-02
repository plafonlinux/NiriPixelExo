from ignis import widgets, utils
from ignis.services.notifications import Notification, NotificationService
from ignis.window_manager import WindowManager
from gi.repository import GLib, Gtk
from ...notifications import ExoNotification

notifications = NotificationService.get_default()
window_manager = WindowManager.get_default()


class AppGroup(widgets.Box):
    """Groups notifications from the same app with collapse/expand."""

    def __init__(self, notification: Notification):
        self._items: list[tuple[Notification, widgets.Revealer]] = []
        self._on_empty_cbs: list = []
        self._expanded = False

        self._list_box = widgets.Box(vertical=True, spacing=2)
        self._more_btn = widgets.Button(
            css_classes=["notification-group-more"],
            visible=False,
            hexpand=True,
            on_click=lambda _: self._toggle_expand(),
        )
        self._more_label = widgets.Label(halign="center", css_classes=["notification-group-more-label"])
        self._more_btn.set_child(self._more_label)

        super().__init__(
            vertical=True,
            css_classes=["notification-group"],
            spacing=2,
            child=[self._list_box, self._more_btn],
        )
        self._add_item(notification, prepend=False)

    def connect_on_empty(self, cb) -> None:
        self._on_empty_cbs.append(cb)

    @property
    def is_empty(self) -> bool:
        return len(self._items) == 0

    def add_new(self, notification: Notification) -> None:
        """Add a newly arrived notification (goes to top, animated)."""
        item = ExoNotification(notification)
        revealer = widgets.Revealer(
            child=item,
            transition_type="slide_down",
            reveal_child=False,
        )
        self._items.insert(0, (notification, revealer))
        self._list_box.prepend(revealer)
        revealer.reveal_child = True
        notification.connect("closed", lambda _: self._on_closed(notification, revealer))
        self._refresh_ui()

    def add_old(self, notification: Notification) -> None:
        """Add an older notification during initial load (appended, no animation)."""
        self._add_item(notification, prepend=False)

    def _add_item(self, notification: Notification, prepend: bool) -> None:
        item = ExoNotification(notification)
        revealer = widgets.Revealer(
            child=item,
            transition_type="slide_down",
            reveal_child=True,
        )
        if prepend:
            self._items.insert(0, (notification, revealer))
            self._list_box.prepend(revealer)
        else:
            self._items.append((notification, revealer))
            self._list_box.append(revealer)
        notification.connect("closed", lambda _: self._on_closed(notification, revealer))
        self._refresh_ui()

    def _on_closed(self, notification: Notification, revealer: widgets.Revealer) -> None:
        self._items = [(n, r) for n, r in self._items if n is not notification]
        revealer.reveal_child = False
        utils.Timeout(revealer.transition_duration, revealer.unparent)
        if self.is_empty:
            for cb in self._on_empty_cbs:
                cb()
            GLib.idle_add(self.unparent)
        else:
            self._refresh_ui()

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        count = len(self._items)
        if count <= 1:
            self._expanded = False
            self._more_btn.set_visible(False)
            for _, r in self._items:
                r.set_visible(True)
            return
        if self._expanded:
            self._more_label.set_label("Свернуть")
            for _, r in self._items:
                r.set_visible(True)
        else:
            hidden = count - 1
            self._more_label.set_label(f"Ещё {hidden}")
            for i, (_, r) in enumerate(self._items):
                r.set_visible(i == 0)
        self._more_btn.set_visible(True)


class Notifications(widgets.Box):
    def __init__(self):
        self._groups: dict[str, AppGroup] = {}

        super().__init__(
            vertical=True,
            vexpand=True,
            css_classes=["notification-center-content"],
            spacing=4,
        )
        notifications.connect("notified", lambda _, n: self._on_notified(n))

        self._load_existing()

        self.append(
            widgets.Label(
                label="notifications_off",
                valign="end",
                vexpand=True,
                css_classes=["notification-center-info-icon"],
                visible=notifications.bind("notifications", lambda v: len(v) == 0),
            )
        )
        self.append(
            widgets.Label(
                label="Нет уведомлений",
                valign="start",
                vexpand=True,
                css_classes=["notification-center-info-label"],
                visible=notifications.bind("notifications", lambda v: len(v) == 0),
            )
        )

    def _load_existing(self) -> None:
        # Group notifications by app, preserving newest-first order
        groups_ordered: list[tuple[str, list[Notification]]] = []
        seen: dict[str, int] = {}
        for n in notifications.notifications:  # newest first
            key = (n.app_name or "").lower()
            if key not in seen:
                seen[key] = len(groups_ordered)
                groups_ordered.append((key, []))
            groups_ordered[seen[key]][1].append(n)

        # Prepend from oldest group to newest so newest ends on top
        for key, notifs in reversed(groups_ordered):
            group = AppGroup(notifs[0])
            for n in notifs[1:]:
                group.add_old(n)
            group.connect_on_empty(lambda k=key: self._groups.pop(k, None))
            self._groups[key] = group
            self.prepend(group)

    def _on_notified(self, notification: Notification) -> None:
        key = (notification.app_name or "").lower()
        existing = self._groups.get(key)
        if existing and not existing.is_empty:
            existing.add_new(notification)
        else:
            group = AppGroup(notification)
            group.connect_on_empty(lambda k=key: self._groups.pop(k, None))
            self._groups[key] = group
            self.prepend(group)


class NotificationCenter(widgets.Box):
    __gtype_name__ = "NotificationCenter"

    def __init__(self):
        scroll = widgets.Scroll(child=Notifications(), height_request=380)
        scroll.set_overflow(Gtk.Overflow.HIDDEN)

        super().__init__(
            vertical=True,
            css_classes=["notification-center"],
            spacing=10,
            child=[scroll],
        )
