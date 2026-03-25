# Changelog

## V1.4.0 - 2026-03-24

- Added a Windows-style menu bar with About, tray actions and keyboard accelerators.
- Added a non-blocking audio worker so the GUI stays responsive while the app is active.
- Added an Fn Capture Lab window to inspect raw keyboard events and diagnose whether `Fn` reaches Windows.
- Surfaced versioning more prominently inside the GUI and kept exit controls visible in multiple places.
- Added release automation on `main` to build, tag and publish the current executable with changelog notes.
- Aligned embedded metadata and About dialog text with the Apache License 2.0 project license.

## V1.3.0 - 2026-03-24

- Added a circular volume dial with live drag and click interaction inside the GUI.
- Expanded persistence into `config.json` for volume, enabled state and editable hotkeys.
- Replaced the exit shortcut strategy to avoid the `Ctrl+Esc` Start-menu conflict and added a tray hotkey.
- Opened the full volume range to 0-100% and aligned the visual meters with that range.

## V1.2.0 - 2026-03-24

- Reworked the desktop interface with a futuristic HUD-style layout.
- Added a custom output matrix for volume control with click-to-set behavior.
- Kept system tray behavior and silent launch flow aligned with the visual redesign.

## V1.1.0 - 2026-03-24

- Added the first GUI with tray integration and silent windowed build.
- Expanded key handling coverage for Windows keys, modifiers and extended keys.
