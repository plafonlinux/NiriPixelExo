# ALT Booster

**GTK4/Libadwaita-приложение для настройки ALT Linux.** Версия 5.7-alpha.  
Автор: PLAFON. Лицензия: MIT.  
Репозиторий: `~/altbooster-alpha`

## Запуск

```bash
altbooster                    # полный интерфейс
altbooster -n                 # только Niri (без сайдбара)
altbooster -n --oboi          # Niri → Обои
altbooster -n --pakety        # Niri → Пакеты
altbooster -n --konfigi       # Niri → Конфиги
```

## Табы

| Флаг | Название | Что делает |
|------|----------|------------|
| `-s` | Начало | Обновление системы, зеркала, sudo, TRIM, Nautilus, темы |
| `-n` | Niri | Установка стека Niri, обои, конфиги, редактор config.kdl |
| `-a` | Приложения | Каталог приложений (Flatpak/EPM) из `modules/apps.json` |
| `-e` | Расширения | GNOME Shell Extensions через D-Bus |
| | Flatpak | Управление Flatpak: список, удаление, обновление, remotes |
| | Терминал | Ptyxis, ZSH, zplug, fastfetch, алиасы |
| | AMD Radeon | Разгон GPU, LACT |
| | DaVinci Resolve | Установка и настройка |
| `-m` | Обслуживание | Очистка кэша, пакетов, Btrfs снапшоты |
| `-f` | Твики | Ananicy, sched_ext, System76 Scheduler, NAPD |
| `-t` | TimeSync | BorgBackup (Time Machine): бэкапы, архив, восстановление |

## Архитектура

```
src/
├── altbooster.py          # Точка входа, CLI-флаги, Gtk/Adw.init
├── core/
│   ├── backend.py         # Фасад: реэкспорт всех core API
│   ├── privileges.py      # pkexec bash, whitelist команд, валидация аргументов
│   ├── packages.py        # apt/epm/flatpak: dry-run, предпросмотр
│   ├── checks.py          # Проверки состояния системы
│   ├── gsettings.py       # gsettings/dconf
│   ├── tweaks.py          # Системные твики (vm.dirty, drive menu)
│   ├── borg.py            # BorgBackup: create, list, extract, prune
│   ├── btrfs.py           # Btrfs: снапшоты, systemd timer
│   ├── mirror.py          # Зеркалирование системы (rsync/btrfs send)
│   └── sched_ext.py       # sched_ext ядро
├── ui/
│   ├── window.py          # Главное окно: сайдбар, табы, CSS
│   ├── dynamic_page.py    # JSON-движок: рендерит JSON в GTK
│   ├── rows.py            # SettingRow, AppRow, TaskRow
│   └── widgets.py         # Фабрики виджетов
├── tabs/                  # Реализации табов
│   └── niri/              # Таб Niri
│       ├── niri_settings.py  # GUI-редактор config.kdl (свой KDL-парсер)
│       ├── packages.py       # Установка стека Niri
│       ├── wallpapers.py     # Галерея обоев + awww/waypaper
│       └── configs.py        # Развёртка конфигов (niri/ashell/fuzzel/mako)
└── modules/               # JSON-конфиги для data-driven табов
```

## Модель безопасности (`core/privileges.py`)

- Один персистентный `pkexec bash` на всё приложение
- Whitelist команд (только разрешённые)
- Валидация аргументов (блокирует опасные: `rm --no-preserve-root`, `find -exec`, SUID и т.д.)
- Apt lock detection перед операциями
- Автозапуск polkit-gnome-agent если нет

## Niri-интеграция

- Определяет Niri через `XDG_CURRENT_DESKTOP`, `NIRI_SOCKET`
- Niri-only режим: `altbooster -n` (скрывает сайдбар)
- `niri msg action reload-config` после правок config.kdl
- `install.sh` добавляет polkit-agent в spawn-at-startup при Niri-сессии
- Таб Niri скрывается если не под Niri и не в standalone

## Состояние

- `~/.config/altbooster/state.json` — debounced, атомарная запись (tmp + rename)

## IPC / CLI

**Только CLI-флаги для переключения табов.** Нет D-Bus сервиса, нет UNIX-сокета, нет headless-режима.

## Возможные точки интеграции с Exo/Эхо

1. **Лаунчер в Quick Toggles / Power Menu** — запуск через `.desktop` или `altbooster -n --oboi`
2. **Кнопка «Настроить Niri»** в настройках Эхо → `altbooster -n`
3. **D-Bus сервис** (нужно добавить) — для вызова конкретных действий
4. **Использовать `core/` как библиотеку** — `privileges.py`, `packages.py`, `checks.py` можно импортировать отдельно
5. **Общий `state.json`** — читать статус выполненных твиков/установок

## Сборка

```bash
cd ~/altbooster-alpha
make install      # в /usr (требует root)
make uninstall
make install-locale
pytest            # тесты
ruff check .      # линтер
```
