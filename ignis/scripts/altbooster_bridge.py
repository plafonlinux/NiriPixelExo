import subprocess
import json
import time
import datetime
import threading
from pathlib import Path
from gi.repository import GLib

_AB_SRC = str(Path("/home/plafon/altbooster-alpha/src").resolve())

_updates_cache: dict | None = None
_updates_cache_time: float = 0
_updates_lock = threading.Lock()

_backup_cache: dict | None = None
_backup_cache_time: float = 0
_backup_lock = threading.Lock()

_UPDATES_CACHE_TTL = 3 * 3600
_BACKUP_CACHE_TTL = 30 * 60


def _run(cmd, timeout=30, env=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return r
    except Exception:
        return None


def _read_ab_state():
    state_file = Path.home() / ".config" / "altbooster" / "state.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text())
    except Exception:
        return {}


def get_updates_count() -> dict:
    global _updates_cache, _updates_cache_time

    with _updates_lock:
        if _updates_cache is not None and (time.time() - _updates_cache_time) < _UPDATES_CACHE_TTL:
            return _updates_cache

    r = _run(["apt-get", "-s", "dist-upgrade"])
    count = 0
    if r and r.returncode == 0:
        for line in r.stdout.splitlines():
            if line.startswith("Inst "):
                count += 1

    result = {"count": count}

    with _updates_lock:
        _updates_cache = result
        _updates_cache_time = time.time()

    return result


def get_backup_status() -> dict | None:
    global _backup_cache, _backup_cache_time

    with _backup_lock:
        if _backup_cache is not None and (time.time() - _backup_cache_time) < _BACKUP_CACHE_TTL:
            return _backup_cache

    state = _read_ab_state()
    repo = state.get("borg_repo_path", "")
    if not repo:
        result = None
        with _backup_lock:
            _backup_cache = result
            _backup_cache_time = time.time()
        return result

    passphrase = state.get("borg_passphrase", "")
    env = {"BORG_PASSPHRASE": passphrase} if passphrase else {}
    last_text = "никогда"
    next_text = None

    r = _run(["borg", "list", "--json", repo], env=env)
    if r and r.returncode in (0, 1) and r.stdout.strip():
        try:
            data = json.loads(r.stdout)
            archives = data.get("archives", [])
            if archives:
                latest = max(archives, key=lambda a: a.get("start", ""))
                start = latest.get("start", "")
                if start:
                    try:
                        dt = datetime.datetime.fromisoformat(start)
                        ago = datetime.datetime.now() - dt
                        total_s = int(ago.total_seconds())
                        if total_s < 60:
                            last_text = "только что"
                        elif total_s < 3600:
                            last_text = f"{total_s // 60} мин назад"
                        elif total_s < 86400:
                            last_text = f"{total_s // 3600} ч назад"
                        else:
                            last_text = f"{total_s // 86400} дн назад"
                    except Exception:
                        last_text = start[:16]
        except Exception:
            pass

    r = _run(["systemctl", "--user", "show", "altbooster-backup.timer",
              "--property=NextElapseUSecRealtime"])
    if r and r.returncode == 0 and r.stdout.strip():
        line = r.stdout.strip()
        if "=" in line:
            try:
                usec = int(line.split("=", 1)[1])
                next_dt = datetime.datetime.fromtimestamp(usec / 1_000_000)
                remaining = next_dt - datetime.datetime.now()
                total_s = int(remaining.total_seconds())
                if total_s < 0:
                    next_text = "скоро"
                elif total_s < 3600:
                    next_text = f"через {total_s // 60} мин"
                elif total_s < 86400:
                    next_text = f"через {total_s // 3600} ч"
                else:
                    next_text = f"через {total_s // 86400} дн"
            except Exception:
                pass

    result = {"last": last_text, "next": next_text, "ok": True}

    with _backup_lock:
        _backup_cache = result
        _backup_cache_time = time.time()

    return result


def force_refresh_updates():
    global _updates_cache_time
    with _updates_lock:
        _updates_cache_time = 0


def force_refresh_backup():
    global _backup_cache_time
    with _backup_lock:
        _backup_cache_time = 0
