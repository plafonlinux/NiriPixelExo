# Exo Project Context

## Project Structure
- **Main Directory**: `/home/plafon/Exo`
- **Ignis Config**: `Exo/ignis` (синхронизируется с `~/.config/ignis`)
- **Widgets**:
    - **QuickCenter**: `Exo/ignis/modules/quickcenter/widgets/media_player.py`
    - **Bar**: `Exo/ignis/modules/bar/widgets/media.py`

## Dependencies & Environment
- **Ignis Source**: `/home/plafon/.local/share/ignis-src` (Editable install)
- **Python Path**: включает `~/.local/share/ignis-src`

## MPRIS & Flatpak Fix
- **Status**: Фикс для Flatpak (доступ через `/proc/{pid}/root/tmp/...`) уже добавлен в `~/.local/share/ignis-src/ignis/services/mpris/player.py`.
- **Ashell Logic**: В `ashell` помимо обхода sandbox реализован `inotify` вотчер для `/tmp`, чтобы успевать захватывать временные файлы обложек Chrome до их удаления. В текущей версии `ignis` этот механизм (`inotify`) отсутствует.

## Recent Changes
- Добавлен медиаплеер в выпадающее меню (QuickCenter).
- Увеличена ширина QuickCenter до 450.
- Удалены кастомные кнопки "Alt Zero".

## Commands
- **Restart Panel**: `pkill -f ignis; sleep 1; cd ~/Exo/ignis && ignis init --config config.py &`
