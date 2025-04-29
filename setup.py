import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but might need fine-tuning.
build_exe_options = {
    "packages": ["os", "tkinter", "PIL"],
    "include_files": ["map_data.json", "terrains.json", "terrains1.json"],
    "excludes": [],
}

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="PyHexForge",
    version="1.0",
    description="Hex Map Editor",
    options={"build_exe": build_exe_options},
    executables=[Executable("PyHexForge.py", base=base, icon=None, target_name="PyHexForge.exe")],
)