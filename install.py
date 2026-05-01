#!/usr/bin/env python3
"""
Niri PixelExo (Эхо) — GTK4 установщик
Поддерживает: ALT Linux Sisyphus, ALT Linux p11
Требует: Niri Wayland compositor
"""

import os, sys, json, shutil, subprocess, threading, urllib.request, tempfile, stat
from pathlib import Path

# ── GTK4 bootstrap ─────────────────────────────────────────────────────────────
try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, GLib
except Exception as exc:
    print(f"GTK4 Python-биндинги недоступны: {exc}")
    print("Установи: sudo apt-get install python3-module-gobject")
    sys.exit(1)

# ── Пути ───────────────────────────────────────────────────────────────────────
INSTALLER_DIR = Path(__file__).parent.resolve()
SOURCE_DIR    = INSTALLER_DIR / "ignis"
DEFAULTS_DIR  = INSTALLER_DIR / "exodefaults"
CONFIGS_DIR   = INSTALLER_DIR / "configs"
CONFIG_DEST   = Path.home() / ".config" / "ignis"
NIRI_CFG      = Path.home() / ".config" / "niri" / "config.kdl"
MATUGEN_DEST  = Path.home() / ".config" / "matugen"
LOCAL_BIN     = Path.home() / ".local" / "bin"

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = b"""
window { background-color: #1e1e2e; color: #cdd6f4; }
.page { padding: 40px 48px; }
.hero-title { font-size: 38px; font-weight: 800; color: #cba6f7; }
.hero-sub   { font-size: 13px; color: #a6adc8; }
.badge      { font-size: 11px; color: #89b4fa; background-color: #313244;
              padding: 2px 10px; border-radius: 99px; }
.item-name  { font-size: 13px; font-weight: bold; color: #cdd6f4; }
.item-desc  { font-size: 12px; color: #6c7086; }
.step-lbl   { font-size: 13px; font-weight: bold; color: #89b4fa; }
.log-view   { font-family: monospace; font-size: 11px; padding: 8px;
              background-color: #181825; color: #cdd6f4; }
progressbar > trough > progress { background-color: #cba6f7; }
progressbar > trough { background-color: #313244; min-height: 6px; border-radius: 4px; }
.btn-primary   { background-color: #cba6f7; color: #1e1e2e; font-weight: bold;
                 padding: 9px 22px; border-radius: 8px; border: none; }
.btn-primary:hover   { background-color: #d4b0ff; }
.btn-secondary { background-color: #313244; color: #cdd6f4;
                 padding: 9px 22px; border-radius: 8px; border: none; }
.btn-secondary:hover { background-color: #45475a; }
.folder-path { font-family: monospace; font-size: 12px; color: #89dceb; }
.done-icon   { font-size: 72px; }
.ok-color    { color: #a6e3a1; }
.err-color   { color: #f38ba8; }
.done-title  { font-size: 24px; font-weight: bold; color: #cdd6f4; }
separator    { background-color: #313244; min-height: 1px; margin: 6px 0; }
"""

# ── Определение системы ────────────────────────────────────────────────────────

def _parse_os_release() -> dict:
    data = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip('"')
    except FileNotFoundError:
        pass
    return data

def detect_alt_branch() -> str | None:
    """Возвращает 'sisyphus', 'p11' или None если не ALT Linux."""
    info = _parse_os_release()
    if info.get("ID", "").lower() != "altlinux":
        return None
    # ALT_BRANCH_ID — самый надёжный ключ
    branch = info.get("ALT_BRANCH_ID", "").lower()
    if branch == "sisyphus":
        return "sisyphus"
    if branch.startswith("p"):
        return branch  # p11, p10 и т.д.
    # Запасной — altlinux-release
    try:
        txt = Path("/etc/altlinux-release").read_text().lower()
        if "sisyphus" in txt: return "sisyphus"
        if "p11"      in txt: return "p11"
    except FileNotFoundError:
        pass
    return "unknown"

def detect_compositor() -> str:
    """Возвращает 'niri' или 'unknown'."""
    xdg = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if os.environ.get("NIRI_SOCKET")                  : return "niri"
    if "niri"     in xdg                              : return "niri"
    return "unknown"

# ── Рабочий поток установки ────────────────────────────────────────────────────

class InstallWorker:
    def __init__(self, branch: str, wallpaper_dir: str | None, on_log, on_done,
                 install_kitty: bool = False, install_starship: bool = False):
        self.branch           = branch
        self.wallpaper_dir    = wallpaper_dir
        self.install_kitty    = install_kitty
        self.install_starship = install_starship
        self._log             = on_log
        self._done            = on_done

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    # ── helpers ─────────────────────────────────────────────────────────────

    def _emit(self, text: str):
        GLib.idle_add(self._log, text)

    def _step(self, label: str, fn):
        GLib.idle_add(self._log, f"\n▶ {label}")
        fn()

    def _env_path(self) -> str:
        return f"{LOCAL_BIN}:{os.environ.get('PATH', '')}"

    def _priv(self) -> list[str]:
        for cmd in ("pkexec", "sudo"):
            if shutil.which(cmd):
                return [cmd]
        raise RuntimeError("Не найден pkexec или sudo для установки пакетов")

    def _sh(self, cmd: list, check=True) -> subprocess.CompletedProcess:
        self._emit(f"  $ {' '.join(str(c) for c in cmd)}")
        env = {**os.environ, "PATH": self._env_path()}
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        tail = (r.stdout + r.stderr).strip().splitlines()[-5:]
        for line in tail:
            self._emit(f"  {line}")
        if check and r.returncode != 0:
            raise RuntimeError(
                f"Команда завершилась с ошибкой (код {r.returncode}):\n"
                + "\n".join(tail[-2:])
            )
        return r

    def _apt(self, *pkgs: str):
        self._sh(self._priv() + ["apt-get", "install", "-y"] + list(pkgs))

    def _in_apt(self, pkg: str) -> bool:
        return subprocess.run(["apt-cache", "show", pkg],
                              capture_output=True).returncode == 0

    def _install_bin(self, src: Path, name: str):
        dst = LOCAL_BIN / name
        shutil.copy2(src, dst)
        dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self._emit(f"  Установлен: ~/.local/bin/{name}")

    # ── шаги ────────────────────────────────────────────────────────────────

    def _run(self):
        try:
            self._step("Обновление пакетной базы",    self._s_apt_update)
            self._step("Проверка pip3",               self._s_pip)
            self._step("Системные пакеты",            self._s_system_pkgs)
            self._step("Установка ignis",             self._s_ignis)
            self._step("Установка matugen",           self._s_matugen)
            self._step("Копирование конфигурации",    self._s_copy_config)
            self._step("Дополнительные конфиги",      self._s_extra_configs)
            self._step("Настройка обоев",             self._s_wallpaper)
            self._step("Генерация цветовой схемы",    self._s_colors)
            self._step("Автозапуск в Niri",           self._s_autostart)
            GLib.idle_add(self._done, True, "")
        except Exception as exc:
            GLib.idle_add(self._done, False, str(exc))

    def _s_system_pkgs(self):
        # (binary, label, apt_candidates, cargo_crate, gh_repo, optional)
        tools = [
            ("swww",               "swww",               ["swww"],                      "swww",               None,                      False),
            ("brightnessctl",      "brightnessctl",        ["brightnessctl"],              None,                 None,                      False),
            ("swayidle",           "swayidle",            ["swayidle"],                  None,                 None,                      False),
            ("fuzzel",             "fuzzel",              ["fuzzel"],                    None,                 None,                      False),
            ("fastfetch",          "fastfetch",           ["fastfetch"],                 None,                 "fastfetch-cli/fastfetch",  False),
            ("playerctl",          "playerctl",           ["playerctl"],                 None,                 None,                      False),
            ("xwayland-satellite", "xwayland-satellite",  ["xwayland-satellite"],        "xwayland-satellite", None,                      False),
            ("hyprlock",           "hyprlock",            ["hyprlock", "hyprland-lock"], None,                 None,                      False),
            ("kitty",              "kitty",               ["kitty"],                     None,                 None,                      False),
        ]
        if self.install_starship:
            tools.append(
                ("starship", "starship", ["starship"], "starship", None, False)
            )

        for binary, label, apt_names, cargo_crate, gh_repo, optional in tools:
            if shutil.which(binary, path=self._env_path()):
                self._emit(f"  ✓ {label} уже установлен")
                continue

            # 1. apt
            for pkg in apt_names:
                if self._in_apt(pkg):
                    self._emit(f"  apt: {label}")
                    self._apt(pkg)
                    break

            if shutil.which(binary, path=self._env_path()):
                continue

            # 2. GitHub binary
            if gh_repo and self._download_tool_binary(gh_repo, binary, label):
                continue

            # 3. cargo
            if cargo_crate:
                self._emit(f"  cargo install {cargo_crate}…")
                try:
                    if not shutil.which("cargo"):
                        self._apt("rust")
                    self._sh(["cargo", "install", cargo_crate])
                    continue
                except Exception as e:
                    self._emit(f"  cargo не удался: {e}")

            if optional:
                self._emit(f"  ⚠ {label}: пропущен, установите вручную")
            else:
                self._emit(f"  ✗ {label}: не установлен, добавьте вручную")

    def _download_tool_binary(self, repo: str, binary: str, label: str) -> bool:
        """Скачать бинарник из GitHub Releases. Возвращает True при успехе."""
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases/latest",
                headers={"User-Agent": "NiriPixelExo-installer/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                assets = json.loads(r.read()).get("assets", [])
        except Exception as e:
            self._emit(f"  GitHub API недоступен: {e}")
            return False

        if not assets:
            return False

        PREFER = [
            "musl-amd64", "musl_amd64", "x86_64-unknown-linux-musl",
            "linux-amd64", "linux_amd64", "linux-x86_64", "x86_64-linux",
        ]
        EXTS = (".tar.gz", ".tgz", ".zip")

        url = None
        for pattern in PREFER:
            url = next(
                (a["browser_download_url"] for a in assets
                 if pattern in a["name"].lower()
                 and any(a["name"].lower().endswith(e) for e in EXTS)),
                None,
            )
            if url:
                break

        if not url:
            return False

        self._emit(f"  GitHub: {label} — {url.rsplit('/', 1)[-1]}")
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)

        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                arc = tmp / "download"
                urllib.request.urlretrieve(url, arc)
                name_lower = url.lower()

                if name_lower.endswith((".tar.gz", ".tgz")):
                    subprocess.run(["tar", "-xzf", str(arc), "-C", str(tmp)], check=True)
                elif name_lower.endswith(".zip"):
                    subprocess.run(["unzip", "-q", str(arc), "-d", str(tmp)], check=True)
                else:
                    self._install_bin(arc, binary)
                    return True

                for f in sorted(tmp.rglob(binary)):
                    if f.is_file() and f.name == binary:
                        self._install_bin(f, binary)
                        return True
        except Exception as e:
            self._emit(f"  Загрузка не удалась: {e}")

        return False

    def _s_extra_configs(self):
        def copy_if_missing(src: Path, dst: Path):
            if src.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                self._emit(f"  → {dst}")

        def copy_with_backup(src: Path, dst: Path):
            if not src.exists():
                return
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                bak = dst.with_suffix(dst.suffix + ".bak")
                shutil.copy2(dst, bak)
                self._emit(f"  Резервная копия: {bak}")
            shutil.copy2(src, dst)
            self._emit(f"  → {dst}")

        # Niri
        copy_if_missing(CONFIGS_DIR / "niri" / "config.kdl", NIRI_CFG)

        # Matugen config
        copy_if_missing(CONFIGS_DIR / "matugen" / "config.toml", MATUGEN_DEST / "config.toml")

        # Matugen templates (из ignis/matugen/templates/)
        tpl_src = SOURCE_DIR / "matugen" / "templates"
        tpl_dst = MATUGEN_DEST / "templates"
        if tpl_src.exists():
            tpl_dst.mkdir(parents=True, exist_ok=True)
            for f in tpl_src.iterdir():
                if f.is_file():
                    copy_if_missing(f, tpl_dst / f.name)

        # Fuzzel
        copy_if_missing(CONFIGS_DIR / "fuzzel" / "fuzzel.ini",
                        Path.home() / ".config" / "fuzzel" / "fuzzel.ini")

        # Fastfetch
        copy_if_missing(CONFIGS_DIR / "fastfetch" / "config.jsonc",
                        Path.home() / ".config" / "fastfetch" / "config.jsonc")

        # Kitty (по выбору пользователя)
        if self.install_kitty:
            copy_with_backup(CONFIGS_DIR / "kitty" / "kitty.conf",
                             Path.home() / ".config" / "kitty" / "kitty.conf")

        # Starship (по выбору пользователя)
        if self.install_starship:
            star_dst = Path.home() / ".config" / "starship.toml"
            copy_if_missing(CONFIGS_DIR / "starship" / "starship.toml", star_dst)
            self._emit("  Starship: добавь в ~/.bashrc: eval \"$(starship init bash)\"")

    def _s_apt_update(self):
        self._sh(self._priv() + ["apt-get", "update", "-qq"])

    def _s_pip(self):
        if shutil.which("pip3"):
            self._emit("  pip3 уже установлен")
            return
        self._apt("python3-module-pip")

    def _s_ignis(self):
        r = self._sh(["pip3", "show", "ignis"], check=False)
        if r.returncode == 0:
            self._sh(["pip3", "install", "--user", "--upgrade", "ignis"])
        else:
            self._sh(["pip3", "install", "--user", "ignis"])

    def _s_matugen(self):
        if shutil.which("matugen", path=self._env_path()):
            self._emit("  matugen уже установлен")
            return
        # 1. репозиторий
        if self._in_apt("matugen"):
            self._apt("matugen")
            return
        # 2. бинарник с GitHub
        try:
            self._emit("  Загружаю бинарник с GitHub…")
            self._download_matugen()
            return
        except Exception as e:
            self._emit(f"  Загрузка не удалась: {e}")
            self._emit("  Устанавливаю через cargo…")
        # 3. cargo
        if not shutil.which("cargo"):
            self._apt("rust")
        self._sh(["cargo", "install", "matugen"])

    def _download_matugen(self):
        req = urllib.request.Request(
            "https://api.github.com/repos/InioX/matugen/releases/latest",
            headers={"User-Agent": "echo-installer/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            assets = json.loads(r.read()).get("assets", [])

        url = next(
            (a["browser_download_url"] for a in assets
             if "linux" in a["name"].lower() and "x86_64" in a["name"].lower()),
            None,
        )
        if not url:
            raise RuntimeError("Бинарник linux-x86_64 не найден в GitHub releases")

        self._emit(f"  {url.rsplit('/', 1)[-1]}")
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            arc = tmp / "matugen.dl"
            urllib.request.urlretrieve(url, arc)
            name = url.lower()

            if name.endswith((".tar.gz", ".tgz")):
                subprocess.run(["tar", "-xzf", str(arc), "-C", str(tmp)], check=True)
            elif name.endswith(".zip"):
                subprocess.run(["unzip", "-q", str(arc), "-d", str(tmp)], check=True)
            else:
                # голый бинарник
                self._install_bin(arc, "matugen")
                return

            for f in sorted(tmp.rglob("matugen")):
                if f.is_file() and not f.suffix:
                    self._install_bin(f, "matugen")
                    return

            raise RuntimeError("Бинарник не найден в архиве")

    def _s_copy_config(self):
        PROTECTED = {"user_settings.json", "colors.scss"}
        CONFIG_DEST.mkdir(parents=True, exist_ok=True)
        n = 0
        for src in SOURCE_DIR.rglob("*"):
            if "__pycache__" in src.parts:
                continue
            rel = src.relative_to(SOURCE_DIR)
            dst = CONFIG_DEST / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            elif src.is_file():
                if dst.exists() and rel.name in PROTECTED:
                    continue
                shutil.copy2(src, dst)
                n += 1
        self._emit(f"  {n} файлов → {CONFIG_DEST}")
        settings = CONFIG_DEST / "user_settings.json"
        if not settings.exists():
            settings.write_text("{}")

    def _s_wallpaper(self):
        wp_dir = Path.home() / "Pictures" / "Wallpapers"
        wp_dir.mkdir(parents=True, exist_ok=True)
        dst = wp_dir / "default.png"
        if not dst.exists():
            shutil.copy2(DEFAULTS_DIR / "default_wallpaper.png", dst)
        self._emit(f"  Обои: {dst}")

        cfg_path = CONFIG_DEST / "user_settings.json"
        try:
            cfg = json.loads(cfg_path.read_text())
        except Exception:
            cfg = {}
        wc = cfg.setdefault("appearance", {}).setdefault("wallcolors", {})
        wc["wallpaper_path"] = str(dst)
        if self.wallpaper_dir:
            wc["quickselect_path"] = self.wallpaper_dir
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=4))

    def _s_colors(self):
        # preview-colors.scss
        pdst = CONFIG_DEST / "styles" / "preview-colors.scss"
        psrc = DEFAULTS_DIR / "preview-colors.scss"
        if psrc.exists() and not pdst.exists():
            shutil.copy2(psrc, pdst)

        matugen = (shutil.which("matugen", path=self._env_path())
                   or str(LOCAL_BIN / "matugen"))
        wp = Path.home() / "Pictures" / "Wallpapers" / "default.png"
        if wp.exists():
            self._sh([matugen, "image", str(wp)])
        else:
            self._emit("  Обои не найдены — пропускаю генерацию цветов")

    def _s_autostart(self):
        ignis = (shutil.which("ignis", path=self._env_path())
                 or str(LOCAL_BIN / "ignis"))
        cfg  = CONFIG_DEST / "config.py"
        line = f'spawn-at-startup "{ignis}" "run" "{cfg}"'

        if not NIRI_CFG.exists():
            NIRI_CFG.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(DEFAULTS_DIR / "config.kdl", NIRI_CFG)
            self._emit("  Скопирован дефолтный конфиг niri")

        content = NIRI_CFG.read_text()
        if "ignis" in content:
            self._emit("  ignis уже есть в конфиге niri")
            return

        with NIRI_CFG.open("a") as f:
            f.write(f"\n// Эхо — автозапуск\n{line}\n")
        self._emit("  spawn-at-startup добавлен в config.kdl")


# ── Окно установщика ───────────────────────────────────────────────────────────

class InstallerWindow(Gtk.ApplicationWindow):

    def __init__(self, app: Gtk.Application, branch: str):
        super().__init__(application=app, title="Установка Эхо")
        self._branch          = branch
        self._wallpaper_dir   = None
        self._install_kitty   = True
        self._install_starship = True
        self._pulse_id        = None
        self._folder_dlg      = None

        p = Gtk.CssProvider()
        p.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), p, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.set_default_size(640, 540)
        self.set_resizable(False)

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self._stack.set_transition_duration(220)
        self.set_child(self._stack)

        self._stack.add_named(self._pg_welcome(),   "welcome")
        self._stack.add_named(self._pg_wallpaper(), "wallpaper")
        self._stack.add_named(self._pg_extras(),    "extras")
        self._stack.add_named(self._pg_install(),   "install")
        self._stack.add_named(self._pg_done(),      "done")

    # ── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _vbox(spacing=0, **kw) -> Gtk.Box:
        return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing, **kw)

    @staticmethod
    def _hbox(spacing=0, **kw) -> Gtk.Box:
        return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=spacing, **kw)

    @staticmethod
    def _spacer() -> Gtk.Box:
        sp = Gtk.Box()
        sp.set_vexpand(True)
        return sp

    # ── страницы ────────────────────────────────────────────────────────────

    def _pg_welcome(self) -> Gtk.Widget:
        box = self._vbox(spacing=10)
        box.add_css_class("page")

        title = Gtk.Label(label="Эхо")
        title.add_css_class("hero-title")
        title.set_halign(Gtk.Align.CENTER)

        sub = Gtk.Label(label="Niri PixelExo — панель для Wayland / Niri")
        sub.add_css_class("hero-sub")
        sub.set_halign(Gtk.Align.CENTER)

        badge = Gtk.Label(label=f"ALT Linux {self._branch.capitalize()}")
        badge.add_css_class("badge")
        badge.set_halign(Gtk.Align.CENTER)
        badge.set_margin_top(4)

        box.append(title)
        box.append(sub)
        box.append(badge)
        box.append(Gtk.Separator())

        sec = Gtk.Label(label="Что будет установлено")
        sec.add_css_class("step-lbl")
        sec.set_halign(Gtk.Align.START)
        box.append(sec)

        for name, desc in [
            ("ignis",                    "Wayland-шелл на GTK4 (Python) — pip3 install ignis"),
            ("matugen",                  "Генератор цветовых схем — репозиторий / GitHub / cargo"),
            ("swww, fuzzel, brightnessctl…", "Системные утилиты — обои, лаунчер, яркость"),
            ("Конфигурация Эхо",         "Копируется в ~/.config/ignis/"),
            ("Конфиги niri, kitty…",     "Готовая настройка среды (по выбору)"),
            ("Автозапуск",               "spawn-at-startup добавляется в niri config.kdl"),
        ]:
            row = self._hbox(spacing=10)
            row.set_margin_start(4)
            row.set_margin_top(2)
            dot = Gtk.Label(label="●")
            dot.add_css_class("badge")
            col = self._vbox(spacing=1)
            n = Gtk.Label(label=name); n.add_css_class("item-name"); n.set_halign(Gtk.Align.START)
            d = Gtk.Label(label=desc); d.add_css_class("item-desc"); d.set_halign(Gtk.Align.START)
            col.append(n); col.append(d)
            row.append(dot); row.append(col)
            box.append(row)

        box.append(self._spacer())

        btn = Gtk.Button(label="Начать →")
        btn.add_css_class("btn-primary")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda _: self._stack.set_visible_child_name("wallpaper"))
        box.append(btn)
        return box

    def _pg_wallpaper(self) -> Gtk.Widget:
        box = self._vbox(spacing=14)
        box.add_css_class("page")
        box.set_valign(Gtk.Align.CENTER)

        title = Gtk.Label(label="Папка с обоями")
        title.add_css_class("done-title")
        title.set_halign(Gtk.Align.CENTER)

        desc = Gtk.Label(
            label="Укажи папку с обоями для быстрого выбора в настройках.\n"
                  "Можно пропустить — выбрать позже."
        )
        desc.add_css_class("hero-sub")
        desc.set_halign(Gtk.Align.CENTER)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_wrap(True)

        self._folder_lbl = Gtk.Label(label="Папка не выбрана")
        self._folder_lbl.add_css_class("folder-path")
        self._folder_lbl.set_halign(Gtk.Align.CENTER)

        pick = Gtk.Button(label="Выбрать папку…")
        pick.add_css_class("btn-secondary")
        pick.set_halign(Gtk.Align.CENTER)
        pick.connect("clicked", self._choose_folder)

        btns = self._hbox(spacing=12)
        btns.set_halign(Gtk.Align.CENTER)
        btns.set_margin_top(12)
        skip = Gtk.Button(label="Пропустить")
        skip.add_css_class("btn-secondary")
        go = Gtk.Button(label="Установить →")
        go.add_css_class("btn-primary")
        skip.connect("clicked", lambda _: self._stack.set_visible_child_name("extras"))
        go.connect("clicked",   lambda _: self._stack.set_visible_child_name("extras"))
        btns.append(skip)
        btns.append(go)

        for w in (title, desc, self._folder_lbl, pick, btns):
            box.append(w)
        return box

    def _pg_extras(self) -> Gtk.Widget:
        box = self._vbox(spacing=10)
        box.add_css_class("page")
        box.set_valign(Gtk.Align.CENTER)

        title = Gtk.Label(label="Дополнительные компоненты")
        title.add_css_class("done-title")
        title.set_halign(Gtk.Align.CENTER)

        desc = Gtk.Label(label="Установить готовые конфиги для этих инструментов?")
        desc.add_css_class("hero-sub")
        desc.set_halign(Gtk.Align.CENTER)

        box.append(title)
        box.append(desc)
        box.append(Gtk.Separator())

        for attr, label, subdesc in [
            ("_chk_kitty",  "Kitty",    "Тема Catppuccin Mocha, JetBrains Mono, горячие клавиши"),
            ("_chk_star",   "Starship", "Кастомный промпт терминала (требует eval в .bashrc/.zshrc)"),
        ]:
            row = self._hbox(spacing=12)
            row.set_margin_top(6)
            row.set_margin_start(8)
            chk = Gtk.CheckButton()
            chk.set_active(True)
            setattr(self, attr, chk)
            col = self._vbox(spacing=2)
            n = Gtk.Label(label=label)
            n.add_css_class("item-name")
            n.set_halign(Gtk.Align.START)
            d = Gtk.Label(label=subdesc)
            d.add_css_class("item-desc")
            d.set_halign(Gtk.Align.START)
            col.append(n)
            col.append(d)
            row.append(chk)
            row.append(col)
            box.append(row)

        box.append(self._spacer())

        btns = self._hbox(spacing=12)
        btns.set_halign(Gtk.Align.CENTER)

        skip = Gtk.Button(label="Пропустить всё")
        skip.add_css_class("btn-secondary")
        go = Gtk.Button(label="Установить →")
        go.add_css_class("btn-primary")

        def on_go(_):
            self._install_kitty    = self._chk_kitty.get_active()
            self._install_starship = self._chk_star.get_active()
            self._begin_install()

        def on_skip(_):
            self._install_kitty    = False
            self._install_starship = False
            self._begin_install()

        go.connect("clicked", on_go)
        skip.connect("clicked", on_skip)
        btns.append(skip)
        btns.append(go)
        box.append(btns)
        return box

    def _pg_install(self) -> Gtk.Widget:
        box = self._vbox(spacing=8)
        box.add_css_class("page")

        self._step_lbl = Gtk.Label(label="Подготовка…")
        self._step_lbl.add_css_class("step-lbl")
        self._step_lbl.set_halign(Gtk.Align.START)

        self._pbar = Gtk.ProgressBar()
        self._pbar.set_pulse_step(0.04)

        self._log_buf = Gtk.TextBuffer()
        self._end_mark = self._log_buf.create_mark(
            "end", self._log_buf.get_end_iter(), False
        )

        log_view = Gtk.TextView(buffer=self._log_buf)
        log_view.set_editable(False)
        log_view.set_cursor_visible(False)
        log_view.set_monospace(True)
        log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        log_view.add_css_class("log-view")
        self._log_view = log_view

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(log_view)

        for w in (self._step_lbl, self._pbar, scroll):
            box.append(w)
        return box

    def _pg_done(self) -> Gtk.Widget:
        box = self._vbox(spacing=14)
        box.add_css_class("page")
        box.set_valign(Gtk.Align.CENTER)

        self._done_icon = Gtk.Label()
        self._done_icon.add_css_class("done-icon")
        self._done_icon.set_halign(Gtk.Align.CENTER)

        self._done_title = Gtk.Label()
        self._done_title.add_css_class("done-title")
        self._done_title.set_halign(Gtk.Align.CENTER)

        self._done_desc = Gtk.Label()
        self._done_desc.add_css_class("hero-sub")
        self._done_desc.set_halign(Gtk.Align.CENTER)
        self._done_desc.set_justify(Gtk.Justification.CENTER)
        self._done_desc.set_wrap(True)

        btns = self._hbox(spacing=12)
        btns.set_halign(Gtk.Align.CENTER)
        btns.set_margin_top(12)
        self._launch_btn = Gtk.Button(label="Запустить Эхо")
        self._launch_btn.add_css_class("btn-primary")
        self._launch_btn.connect("clicked", self._on_launch)
        close_btn = Gtk.Button(label="Закрыть")
        close_btn.add_css_class("btn-secondary")
        close_btn.connect("clicked", lambda _: self.close())
        btns.append(self._launch_btn)
        btns.append(close_btn)

        for w in (self._done_icon, self._done_title, self._done_desc, btns):
            box.append(w)
        return box

    # ── действия ────────────────────────────────────────────────────────────

    def _choose_folder(self, _):
        dlg = Gtk.FileChooserNative(
            title="Выбери папку с обоями",
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            accept_label="Выбрать",
            cancel_label="Отмена",
        )
        dlg.connect("response", self._on_folder_chosen)
        self._folder_dlg = dlg
        dlg.show()

    def _on_folder_chosen(self, dlg: Gtk.FileChooserNative, response: int):
        if response == Gtk.ResponseType.ACCEPT:
            gf = dlg.get_file()
            if gf:
                self._wallpaper_dir = gf.get_path()
                self._folder_lbl.set_label(self._wallpaper_dir)
        self._folder_dlg = None

    def _begin_install(self):
        self._stack.set_visible_child_name("install")

        def _pulse():
            self._pbar.pulse()
            return GLib.SOURCE_CONTINUE

        self._pulse_id = GLib.timeout_add(60, _pulse)

        InstallWorker(
            branch           = self._branch,
            wallpaper_dir    = self._wallpaper_dir,
            on_log           = self._on_log,
            on_done          = self._on_done,
            install_kitty    = self._install_kitty,
            install_starship = self._install_starship,
        ).start()

    def _on_log(self, text: str):
        it = self._log_buf.get_end_iter()
        self._log_buf.insert(it, text + "\n")
        self._log_buf.move_mark(self._end_mark, self._log_buf.get_end_iter())
        self._log_view.scroll_to_mark(self._end_mark, 0.0, False, 0.0, 1.0)
        if text.startswith("\n▶ "):
            self._step_lbl.set_label(text.strip()[2:].strip())

    def _on_done(self, ok: bool, msg: str):
        if self._pulse_id is not None:
            GLib.source_remove(self._pulse_id)
            self._pulse_id = None
        self._pbar.set_fraction(1.0 if ok else 0.5)

        if ok:
            self._done_icon.set_label("✓")
            self._done_icon.set_css_classes(["done-icon", "ok-color"])
            self._done_title.set_label("Установка завершена!")
            self._done_desc.set_label(
                "Перезапусти сессию Niri — панель запустится автоматически.\n"
                "Или нажми «Запустить Эхо» прямо сейчас."
            )
        else:
            self._done_icon.set_label("✗")
            self._done_icon.set_css_classes(["done-icon", "err-color"])
            self._done_title.set_label("Ошибка установки")
            self._done_desc.set_label(msg)
            self._launch_btn.set_sensitive(False)

        self._stack.set_visible_child_name("done")

    def _on_launch(self, _):
        path = f"{LOCAL_BIN}:{os.environ.get('PATH', '')}"
        ignis = shutil.which("ignis", path=path) or str(LOCAL_BIN / "ignis")
        env   = {**os.environ, "PATH": path}
        subprocess.Popen([ignis, "run", str(CONFIG_DEST / "config.py")], env=env)
        self.close()


# ── Приложение ─────────────────────────────────────────────────────────────────

class InstallerApp(Gtk.Application):
    def __init__(self, branch: str):
        super().__init__(application_id="io.niri.pixelexo.installer")
        self._branch = branch

    def do_activate(self):
        InstallerWindow(self, self._branch).present()


# ── Точка входа ────────────────────────────────────────────────────────────────

def main():
    branch     = detect_alt_branch()
    compositor = detect_compositor()

    if branch is None:
        print("Ошибка: поддерживается только ALT Linux Sisyphus и p11.")
        print("Текущий дистрибутив не поддерживается.")
        sys.exit(1)

    if compositor == "unknown":
        print("Предупреждение: Niri не обнаружен в текущей сессии.")
        print("Если ты настраиваешь систему до первого запуска Niri — продолжай.")

    InstallerApp(branch).run(sys.argv)


if __name__ == "__main__":
    main()
