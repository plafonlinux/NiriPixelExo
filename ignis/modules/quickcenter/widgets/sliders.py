import asyncio
from ignis import widgets
from ignis.services.audio import AudioService
from ignis.services.backlight import BacklightService
from ignis.window_manager import WindowManager

audio = AudioService.get_default()
backlight = BacklightService.get_default()
window_manager = WindowManager.get_default()


def _mute_btn(icon_label: widgets.Label) -> widgets.Button:
    return widgets.Button(
        child=icon_label,
        css_classes=["flat"],
    )


class QuickSliders(widgets.Box):
    def __init__(self):
        children = []

        if audio.speaker:
            self.volume_slider = widgets.Scale(
                min=0, max=100, step=1.0,
                on_change=self._on_volume_slider_changed,
                hexpand=True,
            )
            self.speaker_icon = widgets.Label(css_classes=["m3-icon"])
            btn = _mute_btn(self.speaker_icon)
            btn.connect("clicked", lambda _: self._toggle_mute(audio.speaker))
            children.append(widgets.Box(
                css_classes=["m3-slider"], spacing=12,
                child=[btn, self.volume_slider],
            ))

        if audio.microphone:
            self.mic_slider = widgets.Scale(
                min=0, max=100, step=1.0,
                on_change=self._on_mic_slider_changed,
                hexpand=True,
            )
            self.mic_icon = widgets.Label(css_classes=["m3-icon"])
            btn = _mute_btn(self.mic_icon)
            btn.connect("clicked", lambda _: self._toggle_mute(audio.microphone))
            children.append(widgets.Box(
                css_classes=["m3-slider"], spacing=12,
                child=[btn, self.mic_slider],
            ))

        if backlight.available:
            self.backlight_slider = widgets.Scale(
                min=0, max=100, step=1.0,
                on_change=self._on_backlight_slider_changed,
                hexpand=True,
            )
            children.append(widgets.Box(
                css_classes=["m3-slider"], spacing=12,
                child=[
                    widgets.Label(label="brightness_6", css_classes=["m3-icon"]),
                    self.backlight_slider,
                ],
            ))

        super().__init__(
            css_classes=["quick-sliders-container"],
            hexpand=True, halign="fill",
            spacing=2, vertical=True,
            child=children,
        )

        if audio.speaker:
            audio.speaker.connect("notify::volume",   self._sync_speaker)
            audio.speaker.connect("notify::is-muted", self._sync_speaker)
            self._sync_speaker(audio.speaker)

        if audio.microphone:
            audio.microphone.connect("notify::volume",   self._sync_mic)
            audio.microphone.connect("notify::is-muted", self._sync_mic)
            self._sync_mic(audio.microphone)

        if backlight.available:
            backlight.connect("notify::brightness", self._sync_backlight)
            self._sync_backlight(backlight)

    # ── sync UI from service ─────────────────────────────────────────────────

    def _sync_speaker(self, stream, *_):
        muted = stream.is_muted
        self.speaker_icon.set_label("volume_off" if muted else "volume_up")
        self.volume_slider.set_value(0 if muted else stream.volume)

    def _sync_mic(self, stream, *_):
        muted = stream.is_muted
        self.mic_icon.set_label("mic_off" if muted else "mic")
        self.mic_slider.set_value(0 if muted else max(0.0, stream.volume))

    def _sync_backlight(self, bl, *_):
        self.backlight_slider.set_value((bl.brightness / bl.max_brightness) * 100)

    # ── slider → service ─────────────────────────────────────────────────────

    def _on_volume_slider_changed(self, slider):
        self._suppress_osd()
        audio.speaker.volume = slider.get_value()

    def _on_mic_slider_changed(self, slider):
        audio.microphone.volume = slider.get_value()

    def _on_backlight_slider_changed(self, slider):
        self._suppress_osd()
        backlight.brightness = int((slider.get_value() / 100) * backlight.max_brightness)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _toggle_mute(stream):
        stream.is_muted = not stream.is_muted

    def _suppress_osd(self):
        window_manager.suppress_osd = True
        asyncio.create_task(self._reset_suppress_osd())

    async def _reset_suppress_osd(self):
        await asyncio.sleep(0.1)
        window_manager.suppress_osd = False
