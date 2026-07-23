# Maya AutoRigger

A modular auto-rigger for Autodesk Maya, developed in Python. The current implementation supports biped characters and features a modular architecture for future expansion.

## Features

- Modular rigging architecture
- Automatic skeleton generation from guide locators
- Twist joint support
- Ribbon deformation system
- JSON preset import/export
- PySide6 user interface
- Built for Autodesk Maya


## Requirements

- Autodesk Maya 2026 (tested)
- Python 3
- QuatNodes plugin

## Installation

Place the `autoRigger` folder inside:

```text
Documents/maya/scripts/
```

> **Note:** The folder must be placed in `maya/scripts`, not in a version-specific folder such as `maya/2026/scripts`.

Enable the **QuatNodes** plugin before building a rig, as it is required for the twist joint system.

## Running

Open Maya's Script Editor and run:

```python
from autoRigger.modules.uiModules.UI_launcher import run_autorigger

run_autorigger()
```

## Gallery
TO COME

## Future Work

- Quadruped support
- Creature presets
- Spider rig integration
- Matrix-based implementation