# PyHexForge

A Python-based hexagonal map editor with character integration.

## Features

- Create and edit hexagonal maps with custom terrains
- Customize terrain types with colors and images
- Character system with stats and positioning
- Export maps and character data as JSON
- Seamless integration between map editor and character creator

## Installation

1. Clone this repository
2. Run PyHexForge.py for the map editor
3. Run CharacterForge.py for the character creator

```bash
python PyHexForge.py
python CharacterForge.py
```

## Building a Standalone Executable

The repository includes scripts to build standalone executables:

```bash
# Using PyInstaller (recommended)
./build_exe.bat

# Using cx_Freeze
python setup.py build
```

## Integration

Characters created in CharacterForge can be exported and loaded directly into PyHexForge for visualization on the map.

## License

This project is open source and available for modification and distribution.