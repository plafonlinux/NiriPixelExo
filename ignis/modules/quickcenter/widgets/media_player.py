from ignis import widgets
from ignis.services.mpris import MprisService, MprisPlayer
from gi.repository import GLib, Gtk

mpris = MprisService.get_default()


def _fmt(seconds: int) -> str:
    if seconds < 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _icon_label(name: str) -> widgets.Label:
    return widgets.Label(
        label=name,
        css_classes=["m3-icon"],
        style="font-family: 'Material Symbols Outlined', 'Material Icons Outlined';",
    )


class _PlayerCard(widgets.Box):
    def __init__(self, player: MprisPlayer):
        self._player = player
        self._dragging = False

        self._art = widgets.Icon(pixel_size=72, css_classes=["mp-art"])
        art_box = widgets.Box(css_classes=["mp-art-box"], child=[self._art], valign="start", vexpand=False)

        self._title = widgets.Label(
            css_classes=["mp-title"],
            halign="start",
            ellipsize="end",
            max_width_chars=22,
        )
        self._artist = widgets.Label(
            css_classes=["mp-artist"],
            halign="start",
            ellipsize="end",
            max_width_chars=22,
        )

        self._pos_lbl = widgets.Label(label="0:00", css_classes=["mp-time"])
        self._len_lbl = widgets.Label(label="0:00", css_classes=["mp-time"])
        self._progress = widgets.Scale(
            min=0, max=1, step=0.001,
            hexpand=True,
            css_classes=["mp-progress"],
            on_change=self._on_seek,
        )
        progress_row = widgets.Box(
            css_classes=["mp-progress-row"],
            spacing=6,
            child=[self._pos_lbl, self._progress, self._len_lbl],
        )

        self._play_icon = _icon_label("play_arrow")
        self._prev_btn = widgets.Button(
            css_classes=["mp-btn"],
            child=_icon_label("skip_previous"),
            on_click=lambda _: player.previous(),
        )
        self._play_btn = widgets.Button(
            css_classes=["mp-btn", "mp-btn-play"],
            child=self._play_icon,
            on_click=lambda _: player.play_pause(),
        )
        self._next_btn = widgets.Button(
            css_classes=["mp-btn"],
            child=_icon_label("skip_next"),
            on_click=lambda _: player.next(),
        )
        controls = widgets.Box(
            css_classes=["mp-controls"],
            halign="center",
            spacing=4,
            child=[self._prev_btn, self._play_btn, self._next_btn],
        )

        info = widgets.Box(
            vertical=True,
            valign="start",
            hexpand=True,
            spacing=4,
            child=[self._title, self._artist, progress_row],
        )

        top_row = widgets.Box(spacing=14, child=[art_box, info])

        super().__init__(
            css_classes=["mp-card"],
            vertical=True,
            spacing=6,
            child=[top_row, controls],
        )

        player.connect("notify::title", lambda *_: self._update_meta())
        player.connect("notify::artist", lambda *_: self._update_meta())
        player.connect("notify::art-url", lambda *_: self._update_art())
        player.connect("notify::playback-status", lambda *_: self._update_status())
        player.connect("notify::position", lambda *_: self._update_position())
        player.connect("notify::length", lambda *_: self._update_position())
        player.connect("notify::can-go-previous", lambda *_: self._update_sensitivity())
        player.connect("notify::can-go-next", lambda *_: self._update_sensitivity())

        self._update_meta()
        self._update_art()
        self._update_status()
        self._update_position()
        self._update_sensitivity()

    def _update_meta(self):
        self._title.set_label(self._player.title or "")
        self._artist.set_label(self._player.artist or "")

    def _update_art(self):
        url = self._player.art_url
        self._art.set_image(url if url else "audio-x-generic-symbolic")

    def _update_status(self):
        playing = self._player.playback_status == "Playing"
        self._play_icon.set_label("pause" if playing else "play_arrow")

    def _update_position(self):
        if self._dragging:
            return
        pos = self._player.position or 0
        length = self._player.length or 0
        self._pos_lbl.set_label(_fmt(pos))
        self._len_lbl.set_label(_fmt(length))
        if length > 0:
            self._progress.set_value(pos / length)

    def _update_sensitivity(self):
        self._prev_btn.set_sensitive(bool(self._player.can_go_previous))
        self._next_btn.set_sensitive(bool(self._player.can_go_next))

    def _on_seek(self, scale):
        length = self._player.length or 0
        if length > 0:
            self._dragging = True
            pos = int(scale.get_value() * length)
            self._pos_lbl.set_label(_fmt(pos))
            self._player.position = pos
            GLib.timeout_add(300, self._end_drag)

    def _end_drag(self):
        self._dragging = False
        return False


class MediaPlayerWidget(widgets.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            css_classes=["mp-container"],
            visible=False,
        )
        self._known: set = set()
        mpris.connect("player_added", self._on_player_added)
        mpris.connect("notify::players", lambda *_: self._sync_visibility())
        GLib.idle_add(self._rebuild)

    def _on_player_added(self, _, player: MprisPlayer):
        if id(player) not in self._known:
            self._known.add(id(player))
            card = _PlayerCard(player)
            self.append(card)
            player.connect("closed", lambda *_: GLib.idle_add(self._rebuild))
        self._sync_visibility()

    def _rebuild(self):
        child = self.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.remove(child)
            child = nxt
        self._known.clear()
        for player in mpris.players:
            self._known.add(id(player))
            card = _PlayerCard(player)
            self.append(card)
            player.connect("closed", lambda *_: GLib.idle_add(self._rebuild))
        self._sync_visibility()

    def _sync_visibility(self):
        self.set_visible(bool(mpris.players))
