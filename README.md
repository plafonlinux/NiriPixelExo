<div align="center">

![Эхо](https://github.com/user-attachments/assets/ca159dea-aa7c-4d52-bc65-9129a8c1becf)

**Панель рабочего стола в стиле Material 3 для Niri на ALT Linux**

*Построена на Ignis — современный Wayland-шелл на GTK4*

</div>

---

## Обзор

Эхо — красивая и функциональная панель для Wayland-композитора Niri. Реализует принципы дизайна Material You: динамические цвета под обои, плавные анимации, гибкая настройка модулей прямо из встроенного окна настроек.

### Возможности

- **Material You** — адаптивная цветовая схема генерируется автоматически по обоям
- **Только Wayland** — нативная интеграция с Niri через ignis
- **Гибкая раскладка** — двойная панель, перемещение и скрытие модулей
- **Без правки файлов** — все настройки через графический интерфейс
- **Запись экрана** — встроенный рекордер

---

## Скриншоты

<img width="1920" height="1080" src="https://github.com/user-attachments/assets/c60deecf-02e0-4288-a61d-de355cb12aba" />

<img width="1920" height="1080" src="https://github.com/user-attachments/assets/c65f5bfb-c72d-4f36-bdef-b68613759f59" />

<img width="1920" height="1080" src="https://github.com/user-attachments/assets/286a527a-bd9b-478b-bc1d-d852b7cdbf16" />

<img width="1920" height="1080" src="https://github.com/user-attachments/assets/cccad6cd-8866-40b4-b90a-d36bde8d20c6" />

<img width="1920" height="1080" src="https://github.com/user-attachments/assets/3a02e717-42de-4c5e-9aba-78d9840e5d5a" />

---

## Требования

| | |
|---|---|
| **Дистрибутив** | ALT Linux Sisyphus или p11 |
| **Композитор** | [Niri](https://github.com/YaLTeR/niri) |
| **Python** | 3.10+ (есть в системе) |
| **GTK4 / PyGObject** | `python3-module-gobject` |
| **ignis** | устанавливается автоматически через pip3 |
| **matugen** | устанавливается автоматически (репозиторий / GitHub / cargo) |

---

## Установка

### Через установщик (рекомендуется)

Скачай или склонируй репозиторий, затем запусти установщик двойным кликом на файл **`Установить Эхо.desktop`**, или из терминала:

```bash
python3 install.py
```

Установщик сам:
- установит ignis через `pip3`
- установит matugen (ищет в репозитории ALT, затем берёт бинарник с GitHub, крайний случай — собирает через cargo)
- скопирует конфигурацию в `~/.config/ignis/`
- скопирует дефолтные обои в `~/Pictures/Wallpapers/`
- пропишет автозапуск в `~/.config/niri/config.kdl`

Единственный вопрос, который задаст установщик — папка с твоими обоями (для быстрого выбора в настройках). Можно пропустить.

### Ручная установка

```bash
# Зависимости
sudo apt-get install python3-module-gobject

# ignis
pip3 install --user ignis

# matugen (если нет в репозитории)
# вариант 1: бинарник с GitHub (страница релизов InioX/matugen)
# вариант 2: cargo install matugen

# Конфигурация
mkdir -p ~/.config/ignis
cp -r ignis/. ~/.config/ignis/

# Обои и цвета
matugen image /path/to/wallpaper.jpg

# Автозапуск — добавь в ~/.config/niri/config.kdl:
# spawn-at-startup "ignis" "run" "/home/ИМЯ/.config/ignis/config.py"
```

---

## Обновление

Запусти установщик повторно — он обновит ignis и перекопирует конфигурацию. Файлы `user_settings.json` и `colors.scss` при этом не трогаются (твои настройки сохранятся).

```bash
python3 install.py
```

---

## Горячие клавиши

Добавь в `~/.config/niri/config.kdl`:

```kdl
binds {
    // Лаунчер приложений
    Mod { spawn "ignis" "open-window" "Launcher"; }

    // Окно настроек
    Mod+Comma { spawn "ignis" "open-window" "Settings"; }

    // Меню питания
    Mod+Escape { spawn "ignis" "open-window" "PowerMenu"; }

    // Запись экрана
    Mod+Shift+R { spawn "ignis" "run-command" "recorder-record-screen"; }
    Mod+Shift+S { spawn "ignis" "run-command" "recorder-record-region"; }
    Mod+Shift+W { spawn "ignis" "run-command" "recorder-record-portal"; }
}
```

| Действие | Команда |
|---|---|
| Лаунчер | `ignis open-window Launcher` |
| Настройки | `ignis open-window Settings` |
| Меню питания | `ignis open-window PowerMenu` |
| Запись экрана | `ignis run-command recorder-record-screen` |
| Запись региона | `ignis run-command recorder-record-region` |

---

## Настройка

Всё настраивается через встроенное окно **Настройки Эхо** — ни один конфиг-файл редактировать не нужно.

**Внешний вид**
- Обои + автоматическая генерация цветовой схемы (Material You через matugen)
- Светлая / тёмная тема, авто-тёмная по расписанию
- Цветовые схемы и шрифты

**Интерфейс**
- Позиция панели (верх / низ / лево / право), плавающий режим
- Вторая панель
- Включение / отключение и перемещение модулей: лаунчер, рабочие пространства, часы, медиа, системный трей, температуры и другие
- Углы экрана

**Службы**
- Уведомления: позиция, компактный режим
- OSD (индикатор громкости/яркости)
- Параметры записи экрана

**Сеть и Bluetooth**
- Управление Wi-Fi, Ethernet, Bluetooth прямо из панели настроек

---

## Возможные проблемы

**Панель не запускается:**
```bash
ignis run ~/.config/ignis/config.py
```
Запусти вручную и смотри ошибки в терминале.

**Цвета не меняются после смены обоев:**
- Убедись, что matugen установлен: `matugen --version`
- Попробуй вручную: `matugen image /путь/к/обоям.jpg`

**Ошибка `ModuleNotFoundError: ignis`:**
- ignis установлен через `pip3 --user`, убедись что `~/.local/bin` есть в `$PATH`
- Добавь в `~/.bashrc` или `~/.zshrc`: `export PATH="$HOME/.local/bin:$PATH"`

**GTK-приложения не подхватывают тему:**
- Проверь: `gsettings get org.gnome.desktop.interface gtk-theme`
- Установи: `gsettings set org.gnome.desktop.interface gtk-theme "adw-gtk3"`

---

## Благодарности

- [Ignis](https://github.com/ignis-sh/ignis) — фреймворк, на котором построено Эхо
- [linkfrg](https://github.com/linkfrg/dotfiles) — вдохновение и ориентир
- [Material 3 / Material You](https://m3.material.io/) — принципы дизайна
- [Niri](https://github.com/YaLTeR/niri) — скроллируемый тайловый Wayland-композитор
- [matugen](https://github.com/InioX/matugen) — генератор цветовых схем
