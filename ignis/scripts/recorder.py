import os
from datetime import datetime
import asyncio
from ignis.services.recorder import RecorderService, RecorderConfig
from ignis.command_manager import CommandManager
from ignis.services.recorder.service import RecorderPortalCaptureCanceled
from .send_notification import send_notification
from user_settings import user_settings

command_manager = CommandManager.get_default()
recorder = RecorderService.get_default()
last_recording_path = None
recording_indicator_instance = None
options = user_settings.services.recorder


def set_indicator(indicator):
    global recording_indicator_instance
    recording_indicator_instance = indicator


def _on_recording_started(service):
    global last_recording_path
    if recording_indicator_instance:
        recording_indicator_instance.set_paused(False)
        if user_settings.interface.modules.options.recording_indicator != "never":
            recording_indicator_instance.start_timer()

        if options.start_notification:
            send_notification(
                "Запись начата", f"Сохраняется: {last_recording_path}"
            )


def _on_recording_stopped(service):
    global last_recording_path
    if recording_indicator_instance:
        recording_indicator_instance.stop_timer()
    if last_recording_path:
        if options.stop_notification:
            send_notification(
                "Запись остановлена", f"Сохранено: {last_recording_path}"
            )
    last_recording_path = None


def _update_pause_state():
    if recording_indicator_instance:
        recording_indicator_instance.set_paused(recorder.is_paused)


async def _start_recording_task(source: str, file_path: str, **kwargs):
    global last_recording_path

    rec_config = RecorderConfig(source=source, path=file_path, **kwargs)

    try:
        await recorder.start_recording(config=rec_config)
    except RecorderPortalCaptureCanceled:
        if recording_indicator_instance:
            recording_indicator_instance.stop_timer()
        last_recording_path = None
        send_notification(
            "Запись отменена", "Захват через портал был отменён."
        )
    except Exception as e:
        last_recording_path = None
        send_notification("Ошибка записи", f"Произошла ошибка: {str(e)}")


def _record_source(source: str, *args: str, **kwargs):
    global last_recording_path

    if not recorder.is_available:
        send_notification("Нет рекордера", "gpu-screen-recorder не найден.")
        return

    if recorder.active:
        recorder.stop_recording()
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.expanduser(f"~/Видео/Запись экрана/recording_{timestamp}.mp4")
    last_recording_path = file_path

    asyncio.create_task(
        _start_recording_task(
            source=source,
            file_path=file_path,
            audio_devices=["default_output"] if options.record_audio else None,
            **kwargs,
        )
    )


def stop_recording():
    if recorder.active:
        recorder.stop_recording()


def pause_recording():
    if recorder.active and not recorder.is_paused:
        recorder.pause_recording()
        _update_pause_state()


def unpause_recording():
    if recorder.active and recorder.is_paused:
        recorder.continue_recording()
        _update_pause_state()


def record_screen(*args: str):
    _record_source("screen", *args)


def record_portal(*args: str):
    _record_source("portal", *args)


async def _record_region_task():
    """Selects a region using 'slurp' and starts recording it."""
    try:
        if recorder.active:
            recorder.stop_recording()
            return

        send_notification("Выбор области", "Выделите область для записи.")

        proc = await asyncio.create_subprocess_exec(
            "slurp", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            if proc.returncode == 127:
                send_notification(
                    "Не хватает зависимости",
                    "Утилита slurp не найдена.",
                )
            else:
                send_notification(
                    "Выбор области отменён",
                    "Область не выбрана или произошла ошибка.",
                )
            return

        region_str = stdout.decode().strip()
        if not region_str:
            send_notification("Выбор области отменён", "Область не выбрана.")
            return

        # Reformat the region string from 'X,Y WxH' to 'WxH+X+Y'
        xy, wh = region_str.split(" ")
        x, y = xy.split(",")
        reformatted_region = f"{wh}+{x}+{y}"

        _record_source(source="region", region=reformatted_region)

    except FileNotFoundError:
        send_notification(
            "Не хватает зависимости",
            "Утилита slurp не найдена.",
        )
    except Exception as e:
        send_notification(
            "Ошибка выбора области", f"Произошла ошибка: {str(e)}"
        )


def record_region(*args: str):
    asyncio.create_task(_record_region_task())


def setup_recorder_commands():
    command_manager.add_command(
        command_name="recorder-record-screen",
        callback=record_screen,
    )

    command_manager.add_command(
        command_name="recorder-record-portal",
        callback=record_portal,
    )

    command_manager.add_command(
        command_name="recorder-record-region",
        callback=record_region,
    )


def setup_recorder_signals():
    recorder.connect("recording_started", _on_recording_started)
    recorder.connect("recording_stopped", _on_recording_stopped)


setup_recorder_commands()
setup_recorder_signals()
