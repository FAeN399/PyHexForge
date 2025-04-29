@echo off
echo Building PyHexForge executable with PyInstaller...
python -m PyInstaller --onefile --windowed --add-data "map_data.json;." --add-data "terrains.json;." --add-data "terrains1.json;." PyHexForge.py
echo.
echo If successful, the executable will be in the 'dist' folder.
pause