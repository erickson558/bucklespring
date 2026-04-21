# Changelog

## V1.5.4 - 2026-04-21

- Added start-minimized-to-tray behavior: the main window is now hidden (`withdraw`) before `mainloop()` starts so the app boots silently into the tray without flashing the GUI on screen. Users open the window by double-clicking the tray icon or using the `SEND TO TRAY` hotkey (Ctrl+Alt+H).
- Optimized background animation loop: `_animate_background()` now detects when the window is in `"withdrawn"` state and re-schedules itself at 500 ms instead of 90 ms, eliminating unnecessary canvas draw calls while the app lives in the tray.
- Fixed spurious `_on_unmap` invocations caused by tkinter propagating `<Unmap>` events from child widgets up to the root binding; added an early-exit guard (`_event.widget is not self.root`) so the handler only acts on the root window's own unmap events.

## V1.5.3 - 2026-04-21

- Added `app.log` session log (`%LOCALAPPDATA%\Bucklespring\app.log`) that records startup, normal shutdown, duplicate-instance blocks and unexpected mainloop errors for post-hibernation and post-crash diagnostics.
- Improved single-instance guard: a second launch now attempts to bring the existing window to the foreground via Win32 `FindWindowW`/`ShowWindow`/`SetForegroundWindow`; if the window cannot be found (fully hidden in tray), a brief informative messagebox is shown instead of silently exiting.
- Fixed `_set_volume_and_refresh` calling `save_settings()` twice per volume button press — `set_volume()`/`adjust_volume()` already persist settings internally; the wrapper now only calls `refresh_ui()`.
- Added `bring_existing_instance_to_front()` Win32 helper function with full inline documentation.
- Added `app_log_path()` and `write_app_log()` utilities alongside the existing `error_log_path()`/`write_error_log()` pair.
- Wrapped `app.start()` in `main()` with a try/except to log unexpected mainloop errors to both `app.log` and `error.log`.

## V1.5.2 - 2026-04-20

- Fixed silent startup crash caused by `Global\` mutex failing on standard Windows user accounts without `SeCreateGlobalPrivilege`; the guard now falls back to `Local\` and continues best-effort if both namespaces fail.
- Fixed `keyboard.hook()` being called outside any `try/except` block; an exception here previously terminated `__init__` silently in the windowless `.exe`.
- Wrapped `BucklespringApp()` construction in `main()` with a full `try/except` that shows a tkinter error dialog and writes a detailed traceback to `%LOCALAPPDATA%\Bucklespring\error.log`.
- Added `write_error_log()` utility and `error_log_path()` so all unhandled exceptions are persisted for post-mortem diagnostics when running without a console.
- Fixed `_drain_diagnostic_queue` after-loop ID not being tracked; the loop can now be properly cancelled in `exit_application()` to avoid `TclError` on a destroyed window.
- Added `_tray_started` flag so `refresh_ui()` only calls `tray_icon.update_menu()` and updates `.title` after `run_detached()` has been called.
- Added comprehensive inline and docstring comments throughout all classes and methods.

## V1.5.1 - 2026-03-25

- Hardened the audio worker so a missing or corrupted WAV no longer kills resident playback for the whole session.
- Ignored orphaned key-release events in the sound queue to prevent phantom release clicks when Windows reports `up` without a tracked `down`.
- Added safe configuration persistence fallback to `%LOCALAPPDATA%\\Bucklespring\\config.json` when the app directory is read-only.
- Added regression tests for config fallback loading/saving, worker resilience and stray release filtering.

## V1.5.0 - 2026-03-24

- Added GUI multi-language support with English and Spanish translations for the main window, tray menu, About dialog and Fn Capture Lab.
- Added a language selector to the menu bar and persisted the chosen locale in `config.json` so the app restores it on startup.
- Prepared the release workflow for GitHub's Node 24 runtime while keeping automatic build, tag and release creation on `main`.

## V1.4.1 - 2026-03-24

- Fixed the GitHub Actions workflow parsing so releases can be built and published from `main` without startup failure.
- Rebuilt the executable and aligned the patch version across the app, README, tag metadata and embedded Windows version info.

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
