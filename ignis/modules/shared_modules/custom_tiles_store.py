import json
import os

_FILE = os.path.expanduser("~/.config/ignis/custom_tiles.json")
_listeners: list = []


def _load() -> list[dict]:
    try:
        with open(_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(tiles: list[dict]) -> None:
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(tiles, f, ensure_ascii=False, indent=2)


def get_tiles() -> list[dict]:
    return _load()


def add_tile(icon: str, label: str, command: str) -> None:
    tiles = _load()
    tiles.append({"icon": icon.strip(), "label": label.strip(), "command": command.strip()})
    _save(tiles)
    _notify()


def remove_tile(index: int) -> None:
    tiles = _load()
    if 0 <= index < len(tiles):
        tiles.pop(index)
        _save(tiles)
        _notify()


def connect_changed(callback) -> None:
    _listeners.append(callback)


def disconnect_changed(callback) -> None:
    if callback in _listeners:
        _listeners.remove(callback)


def _notify() -> None:
    for cb in list(_listeners):
        cb()
