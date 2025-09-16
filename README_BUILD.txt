# Инструкция по сборке проекта Cursor Trail с помощью PyInstaller

1. Откройте PowerShell или cmd в папке проекта:
   cd "C:\Users\User\Documents\Cursor Trail"

2. Установите PyInstaller (если не установлен):
   pip install pyinstaller

3. ВАЖНО: Команду pyinstaller нужно вводить одной строкой!  
   Символ ^ — это перенос строки, он работает только если вы весь блок вставляете сразу,  
   либо пишите всё в одну строку.

   Пример для PowerShell/Windows — всё одной строкой:
   ```
   pyinstaller --onefile --windowed --icon=icon.ico --add-data "light_theme.py;." --add-data "dark_theme.py;." --add-data "localization.json;." --add-data "settings.json;." --add-data "icon.ico;." cursor_trail_qt.py
   ```

   Если вы копируете из инструкции с переносами (^), убедитесь, что вставляете всю команду сразу, либо пишите как выше.

4. После сборки файл появится в папке dist:
   dist\cursor_trail_qt.exe

5. Для запуска:
   dist\cursor_trail_qt.exe

# Все необходимые файлы (light_theme.py, dark_theme.py, localization.json, settings.json, icon.ico)
# должны лежать в папке с исходником cursor_trail_qt.py.
