from __future__ import annotations

import argparse
import atexit
import ctypes
import json
import math
import os
import queue
import sys
import threading
import tkinter as tk
import warnings
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from tkinter import messagebox, scrolledtext
from typing import Callable

import keyboard
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import pygame
import pystray
from PIL import Image, ImageDraw

from version import APP_AUTHOR, APP_LICENSE, APP_NAME, APP_VERSION


DEFAULT_VOLUME = 0.10
MIN_VOLUME = 0.0
MAX_VOLUME = 1.0
VOLUME_STEP = 0.05
CONFIG_FILE_NAME = "config.json"
LEGACY_CONFIG_FILE = Path.home() / ".keyboard_sounds_config.json"
TRAY_TITLE = f"{APP_NAME} {APP_VERSION}"
UNKNOWN_STEM = "ff"
ICON_FILE_NAME = "bucklespring.ico"
MUTEX_NAME = f"Global\\{APP_NAME}-{APP_VERSION}"
BACKGROUND_LAYER_TOP = "#07161d"
BACKGROUND_LAYER_BOTTOM = "#03090d"
PANEL_COLOR = "#0a1c24"
PANEL_ALT_COLOR = "#0f2832"
TEXT_PRIMARY = "#f2fffb"
TEXT_MUTED = "#74a3a6"
ACCENT_CYAN = "#37f3ff"
ACCENT_GREEN = "#8effb3"
ACCENT_ORANGE = "#ff9b54"
ACCENT_RED = "#ff5f71"
GRID_LINE = "#12323e"
HOTKEY_FIELDS = (
    ("toggle_enabled", "TOGGLE ENGINE", "Activa o silencia el motor", "ctrl+alt+m"),
    ("volume_up", "VOLUME UP", "Sube el nivel de salida", "ctrl+alt+up"),
    ("volume_down", "VOLUME DOWN", "Reduce el nivel de salida", "ctrl+alt+down"),
    ("hide_window", "SEND TO TRAY", "Oculta la ventana y deja el icono residente", "ctrl+alt+h"),
    ("exit_application", "EXIT SESSION", "Cierra por completo la aplicación residente", "ctrl+alt+q"),
)
DEFAULT_HOTKEYS = {action: hotkey for action, _label, _description, hotkey in HOTKEY_FIELDS}
HOTKEY_LABELS = {action: label for action, label, _description, _hotkey in HOTKEY_FIELDS}
HOTKEY_DESCRIPTIONS = {action: description for action, _label, description, _hotkey in HOTKEY_FIELDS}
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "es")
HOTKEY_TRANSLATIONS = {
    "en": {
        "toggle_enabled": {"label": "TOGGLE ENGINE", "description": "Turn the sound engine on or off"},
        "volume_up": {"label": "VOLUME UP", "description": "Increase output level"},
        "volume_down": {"label": "VOLUME DOWN", "description": "Decrease output level"},
        "hide_window": {"label": "SEND TO TRAY", "description": "Hide the window and keep the tray icon active"},
        "exit_application": {"label": "EXIT SESSION", "description": "Close the resident application completely"},
    },
    "es": {
        "toggle_enabled": {"label": "ACTIVAR MOTOR", "description": "Activa o silencia el motor"},
        "volume_up": {"label": "SUBIR VOLUMEN", "description": "Sube el nivel de salida"},
        "volume_down": {"label": "BAJAR VOLUMEN", "description": "Reduce el nivel de salida"},
        "hide_window": {"label": "ENVIAR AL TRAY", "description": "Oculta la ventana y deja el icono residente"},
        "exit_application": {"label": "CERRAR SESION", "description": "Cierra por completo la aplicacion residente"},
    },
}
TRANSLATIONS = {
    "en": {
        "panel_engine_title": "ACOUSTIC TYPE ENGINE",
        "panel_engine_subtitle": "Realtime resident keyboard ambience",
        "panel_controls_title": "CONTROL CORE",
        "panel_controls_subtitle": "Manual override",
        "panel_output_title": "OUTPUT MATRIX",
        "panel_output_subtitle": "Click the bars to set intensity",
        "hero_tagline": "Future mechanical type ambience for Windows",
        "build_signature": "ASYNC AUDIO / TRAY ONLINE / HOTKEYS CONFIGURABLE",
        "version_chip": "VERSION {version}",
        "button_send_to_tray": "SEND TO TRAY",
        "button_exit_application": "EXIT APPLICATION",
        "button_minimize_to_tray": "MINIMIZE TO TRAY",
        "button_exit_session": "EXIT SESSION",
        "section_command_keys": "COMMAND KEYS",
        "config_saved_in": "Persistent profile saved in {config_name}",
        "button_apply_hotkeys": "APPLY HOTKEYS",
        "button_reset_defaults": "RESET DEFAULTS",
        "button_fn_lab": "FN CAPTURE LAB",
        "button_about": "ABOUT",
        "output_hint": "Dial the ring or click the bars to set live output with exact persistence.",
        "output_state_active": "TRAY MIRROR ACTIVE",
        "output_state_muted": "AUDIO PATH MUTED",
        "output_tray_label": "TRAY",
        "output_exit_label": "EXIT",
        "button_decrease_volume": "- 5%",
        "button_increase_volume": "+ 5%",
        "menu_file": "File",
        "menu_settings": "Settings",
        "menu_language": "Language",
        "menu_help": "Help",
        "menu_file_send_to_tray": "Send to tray",
        "menu_file_show_window": "Show window",
        "menu_file_exit": "Exit",
        "menu_settings_apply_hotkeys": "Apply hotkeys",
        "menu_settings_reset_hotkeys": "Reset hotkeys",
        "menu_settings_fn_lab": "Fn Capture Lab",
        "menu_help_about": "About {version}",
        "language_option_en": "English",
        "language_option_es": "Spanish",
        "status_word_active": "ACTIVE",
        "status_word_muted": "MUTED",
        "toggle_deactivate": "DEACTIVATE ENGINE",
        "toggle_reactivate": "REACTIVATE ENGINE",
        "mixer_online": "audio bus online",
        "mixer_unavailable": "audio bus unavailable",
        "status_summary": "Engine status: {status}\nMixer: {mixer}\nConfig: {config_name}",
        "substatus_summary": "resident keyboard hook / tray armed / non-blocking audio path",
        "health_hook_live": "HOOK LIVE",
        "health_hook_idle": "HOOK IDLE",
        "health_tray_ready": "TRAY READY",
        "health_async_audio": "ASYNC AUDIO",
        "volume_output_level": "OUTPUT LEVEL  {volume:03d}%",
        "window_tray_hint": "Window close or minimize sends the app to tray.\n{summary}",
        "hotkeys_persisted": "Hotkeys persisted in {config_name} and reloaded on startup.",
        "hotkeys_applied": "Hotkeys applied and saved in {config_name}.",
        "hotkeys_reset": "Default hotkeys restored.",
        "hotkeys_apply_error": "Could not apply hotkeys: {error}",
        "hotkeys_reset_error": "Could not restore default hotkeys: {error}",
        "hotkey_requires_valid": "{label} requires a valid shortcut.",
        "hotkey_duplicate": "Shortcut {hotkey} is duplicated.",
        "hotkey_empty": "Shortcut for {label} cannot be empty.",
        "tray_title_active": "Active",
        "tray_title_muted": "Muted",
        "tray_menu_show_window": "Show window",
        "tray_menu_sound_active": "Sound active",
        "tray_menu_exit": "Exit",
        "fn_capture_window_title": "{app_name} {version} - Fn Capture Lab",
        "fn_capture_heading": "FN CAPTURE LAB",
        "fn_capture_description": "Press Fn, Fn+another key or any special key. If Windows reports the event, it will appear here with its name and scan code.",
        "fn_capture_clear": "CLEAR LOG",
        "fn_capture_copy": "COPY LOG",
        "fn_capture_close": "CLOSE",
        "fn_capture_status_intro": "Press Fn and other keys to inspect name, scan code and event type.",
        "fn_capture_status_no_event": "Press Fn. If no event appears, the keyboard firmware is not exposing it to Windows.",
        "fn_capture_status_detected": "Fn was detected by Windows. You can map it using the event shown above.",
        "fn_capture_status_hidden": "Press Fn. If no new row appears, the keyboard firmware is consuming it.",
        "fn_capture_status_no_entries": "There are no captured events to copy yet.",
        "fn_capture_status_copied": "Capture log copied to the clipboard.",
        "fn_missing_name": "(unnamed)",
        "diag_field_type": "type",
        "diag_field_scan": "scan",
        "diag_field_name": "name",
        "about_title": "About {app_name}",
        "about_message": "{app_name} {version}\nAuthor: {author}\nLicense: {license}\nCopyright (c) {year} {author}",
        "volume_meter_title": "AMPLITUDE BUS",
        "volume_meter_footer": "VECTOR OUTPUT",
        "output_dial_title": "OUTPUT DIAL",
    },
    "es": {
        "panel_engine_title": "MOTOR ACUSTICO",
        "panel_engine_subtitle": "Ambiente residente de teclado en tiempo real",
        "panel_controls_title": "NUCLEO DE CONTROL",
        "panel_controls_subtitle": "Control manual",
        "panel_output_title": "MATRIZ DE SALIDA",
        "panel_output_subtitle": "Haz clic en las barras para ajustar la intensidad",
        "hero_tagline": "Ambiente mecanico futurista para teclados en Windows",
        "build_signature": "AUDIO ASINCRONO / TRAY ACTIVO / ATAJOS CONFIGURABLES",
        "version_chip": "VERSION {version}",
        "button_send_to_tray": "ENVIAR AL TRAY",
        "button_exit_application": "SALIR DE LA APP",
        "button_minimize_to_tray": "MINIMIZAR AL TRAY",
        "button_exit_session": "CERRAR SESION",
        "section_command_keys": "ATAJOS",
        "config_saved_in": "Perfil persistente guardado en {config_name}",
        "button_apply_hotkeys": "APLICAR ATAJOS",
        "button_reset_defaults": "RESTAURAR ATAJOS",
        "button_fn_lab": "LABORATORIO FN",
        "button_about": "ACERCA DE",
        "output_hint": "Gira el anillo o haz clic en las barras para ajustar la salida en vivo con persistencia exacta.",
        "output_state_active": "MODO TRAY ACTIVO",
        "output_state_muted": "RUTA DE AUDIO SILENCIADA",
        "output_tray_label": "TRAY",
        "output_exit_label": "SALIR",
        "button_decrease_volume": "- 5%",
        "button_increase_volume": "+ 5%",
        "menu_file": "Archivo",
        "menu_settings": "Configuracion",
        "menu_language": "Idioma",
        "menu_help": "Ayuda",
        "menu_file_send_to_tray": "Enviar al tray",
        "menu_file_show_window": "Mostrar ventana",
        "menu_file_exit": "Salir",
        "menu_settings_apply_hotkeys": "Aplicar atajos",
        "menu_settings_reset_hotkeys": "Restaurar atajos",
        "menu_settings_fn_lab": "Laboratorio Fn",
        "menu_help_about": "Acerca de {version}",
        "language_option_en": "Ingles",
        "language_option_es": "Espanol",
        "status_word_active": "ACTIVO",
        "status_word_muted": "SILENCIADO",
        "toggle_deactivate": "DESACTIVAR MOTOR",
        "toggle_reactivate": "REACTIVAR MOTOR",
        "mixer_online": "bus de audio en linea",
        "mixer_unavailable": "bus de audio no disponible",
        "status_summary": "Estado del motor: {status}\nMixer: {mixer}\nConfig: {config_name}",
        "substatus_summary": "hook residente de teclado / tray armado / ruta de audio no bloqueante",
        "health_hook_live": "HOOK ACTIVO",
        "health_hook_idle": "HOOK EN PAUSA",
        "health_tray_ready": "TRAY LISTO",
        "health_async_audio": "AUDIO ASINCRONO",
        "volume_output_level": "NIVEL DE SALIDA  {volume:03d}%",
        "window_tray_hint": "Cerrar o minimizar envia la app a la bandeja.\n{summary}",
        "hotkeys_persisted": "Los atajos se guardaron en {config_name} y se recargan al iniciar.",
        "hotkeys_applied": "Atajos aplicados y guardados en {config_name}.",
        "hotkeys_reset": "Atajos por defecto restaurados.",
        "hotkeys_apply_error": "No se pudieron aplicar los atajos: {error}",
        "hotkeys_reset_error": "No se pudieron restaurar los atajos por defecto: {error}",
        "hotkey_requires_valid": "{label} requiere un atajo valido.",
        "hotkey_duplicate": "El atajo {hotkey} esta repetido.",
        "hotkey_empty": "El atajo para {label} no puede quedar vacio.",
        "tray_title_active": "Activo",
        "tray_title_muted": "Silenciado",
        "tray_menu_show_window": "Mostrar ventana",
        "tray_menu_sound_active": "Sonido activo",
        "tray_menu_exit": "Salir",
        "fn_capture_window_title": "{app_name} {version} - Laboratorio Fn",
        "fn_capture_heading": "LABORATORIO FN",
        "fn_capture_description": "Presiona Fn, Fn+otra tecla o cualquier tecla especial. Si Windows reporta el evento, quedara registrado aqui con nombre y scan code.",
        "fn_capture_clear": "LIMPIAR LOG",
        "fn_capture_copy": "COPIAR LOG",
        "fn_capture_close": "CERRAR",
        "fn_capture_status_intro": "Presiona Fn y otras teclas para inspeccionar nombre, scan code y tipo de evento.",
        "fn_capture_status_no_event": "Presiona Fn. Si no aparece ningun evento, el teclado no la expone a Windows.",
        "fn_capture_status_detected": "Fn fue detectada por Windows. Ya puedes mapearla con el evento real mostrado arriba.",
        "fn_capture_status_hidden": "Presiona Fn. Si no aparece ninguna fila nueva, el firmware del teclado la esta consumiendo.",
        "fn_capture_status_no_entries": "Todavia no hay eventos para copiar.",
        "fn_capture_status_copied": "Log de captura copiado al portapapeles.",
        "fn_missing_name": "(sin nombre)",
        "diag_field_type": "tipo",
        "diag_field_scan": "scan",
        "diag_field_name": "nombre",
        "about_title": "Acerca de {app_name}",
        "about_message": "{app_name} {version}\nAutor: {author}\nLicencia: {license}\nCopyright (c) {year} {author}",
        "volume_meter_title": "BUS DE AMPLITUD",
        "volume_meter_footer": "SALIDA VECTORIAL",
        "output_dial_title": "DIAL DE SALIDA",
    },
}

KEY_NAME_OVERRIDES = {
    "right windows": "61",
    "right windows key": "61",
    "right alt": "61",
    "alt gr": "61",
    "altgr": "61",
    "menu": "63",
    "application": "63",
    "apps": "63",
    "right shift": "66",
    "right ctrl": "67",
    "up": "6a",
    "up arrow": "6a",
    "down": "6b",
    "down arrow": "6b",
    "right": "6c",
    "right arrow": "6c",
    "left": "6d",
    "left arrow": "6d",
    "num lock": "6e",
    "print screen": "6f",
    "printscreen": "6f",
    "pause": "77",
}

KEY_NAME_FALLBACKS = {
    "left windows": "5b",
    "windows": "5b",
    "left ctrl": "1d",
    "left shift": "2a",
    "left alt": "38",
    "spacebar": "39",
    "page up": "49",
    "page down": "51",
    "home": "47",
    "end": "4f",
    "insert": "52",
    "delete": "53",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bucklespring keyboard sound app")
    parser.add_argument("--version", action="store_true", help="Print the current version and exit")
    return parser.parse_args()


def bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resolve_config_path() -> Path:
    return app_root() / CONFIG_FILE_NAME


def fallback_config_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    base_dir = Path(local_appdata) if local_appdata else Path.home() / "AppData" / "Local"
    return base_dir / APP_NAME / CONFIG_FILE_NAME


def iter_config_paths(*preferred_paths: Path) -> tuple[Path, ...]:
    candidates: list[Path] = []
    seen: set[str] = set()
    for path in (*preferred_paths, resolve_config_path(), fallback_config_path(), LEGACY_CONFIG_FILE):
        key = os.path.normcase(str(path.resolve(strict=False)))
        if key in seen:
            continue
        seen.add(key)
        candidates.append(path)
    return tuple(candidates)


def resolve_audio_dir() -> Path:
    external = app_root() / "audios"
    bundled = bundle_root() / "audios"
    if external.exists():
        return external
    return bundled


def resolve_icon_path() -> Path:
    external = app_root() / ICON_FILE_NAME
    bundled = bundle_root() / ICON_FILE_NAME
    if external.exists():
        return external
    return bundled


def clamp(value: float, minimum: float = MIN_VOLUME, maximum: float = MAX_VOLUME) -> float:
    return max(minimum, min(maximum, value))


def normalize_name(name: str | None) -> str:
    return (name or "").strip().lower()


def normalize_hotkey(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    parts: list[str] = []
    for raw_part in value.split("+"):
        token = " ".join(raw_part.strip().lower().split())
        if token:
            parts.append(token)

    if not parts:
        return None
    return "+".join(parts)


def normalize_language(value: object) -> str:
    if isinstance(value, str):
        candidate = value.strip().lower()
        if candidate in SUPPORTED_LANGUAGES:
            return candidate
    return DEFAULT_LANGUAGE


def format_hotkey(value: str) -> str:
    return " + ".join(part.upper() for part in value.split("+"))


@dataclass(frozen=True)
class KeyEventSnapshot:
    name: str | None
    scan_code: int | None
    event_type: str


class SingleInstanceGuard:
    ERROR_ALREADY_EXISTS = 183

    def __init__(self, name: str) -> None:
        self.name = name
        self.handle = None
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        self.kernel32.CreateMutexW.restype = ctypes.c_void_p
        self.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        self.kernel32.CloseHandle.restype = ctypes.c_bool

    def acquire(self) -> bool:
        self.handle = self.kernel32.CreateMutexW(None, False, self.name)
        if not self.handle:
            raise OSError("Could not create the single-instance mutex.")
        return ctypes.get_last_error() != self.ERROR_ALREADY_EXISTS

    def release(self) -> None:
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


class SoundEngine:
    def __init__(self) -> None:
        self.audio_dir = resolve_audio_dir()
        self.config_path = resolve_config_path()
        self.volume = DEFAULT_VOLUME
        self.enabled = True
        self.language = DEFAULT_LANGUAGE
        self.hotkeys = dict(DEFAULT_HOTKEYS)
        self.pressed_keys: set[tuple[int | None, str, str]] = set()
        self.sound_files = self._discover_sound_files()
        self.sound_cache: dict[Path, pygame.mixer.Sound] = {}
        self.failed_sound_paths: set[Path] = set()
        self.cache_lock = threading.Lock()
        self.audio_queue: queue.Queue[KeyEventSnapshot | None] = queue.Queue()
        self.event_observers: list[Callable[[KeyEventSnapshot], None]] = []
        self.worker_stop = threading.Event()
        self.mixer_ready = False
        self.last_audio_error: str | None = None
        self.last_config_error: str | None = None
        self._setup_mixer()
        self.load_settings()
        self.audio_worker = threading.Thread(target=self._audio_worker_loop, name="bucklespring-audio", daemon=True)
        self.audio_worker.start()

    def _setup_mixer(self) -> None:
        try:
            pygame.mixer.pre_init(44100, -16, 2, 256)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(64)
            self.mixer_ready = True
        except pygame.error:
            self.mixer_ready = False

    def _discover_sound_files(self) -> dict[str, dict[str, Path]]:
        sound_files: dict[str, dict[str, Path]] = {}
        if not self.audio_dir.exists():
            return sound_files

        for path in sorted(self.audio_dir.glob("*.wav")):
            parts = path.stem.split("-")
            if len(parts) != 2:
                continue
            stem, suffix = parts
            if suffix not in {"0", "1"}:
                continue
            sound_files.setdefault(stem.lower(), {})["press" if suffix == "0" else "release"] = path
        return sound_files

    def _load_sound(self, path: Path) -> pygame.mixer.Sound | None:
        with self.cache_lock:
            if path in self.failed_sound_paths:
                return None
            sound = self.sound_cache.get(path)
            if sound is None:
                try:
                    sound = pygame.mixer.Sound(str(path))
                except Exception as exc:
                    self.failed_sound_paths.add(path)
                    self.last_audio_error = f"{path.name}: {exc}"
                    return None
                self.sound_cache[path] = sound
            return sound

    def _play_sound_path(self, path: Path) -> bool:
        sound = self._load_sound(path)
        if sound is None:
            return False

        try:
            sound.set_volume(self.volume)
            sound.play()
        except Exception as exc:
            with self.cache_lock:
                self.sound_cache.pop(path, None)
                self.failed_sound_paths.add(path)
            self.last_audio_error = f"{path.name}: {exc}"
            return False

        self.last_audio_error = None
        return True

    def _audio_worker_loop(self) -> None:
        while not self.worker_stop.is_set():
            snapshot = self.audio_queue.get()
            if snapshot is None:
                break
            try:
                # Keep the resident worker alive even if a single asset is missing or corrupted.
                self.play_for_event(snapshot)
            except Exception as exc:
                self.last_audio_error = str(exc)

    def add_event_observer(self, callback: Callable[[KeyEventSnapshot], None]) -> None:
        self.event_observers.append(callback)

    def _emit_event(self, snapshot: KeyEventSnapshot) -> None:
        for callback in list(self.event_observers):
            try:
                callback(snapshot)
            except Exception:
                continue

    def _snapshot_from_event(self, event: keyboard.KeyboardEvent) -> KeyEventSnapshot:
        return KeyEventSnapshot(
            name=getattr(event, "name", None),
            scan_code=getattr(event, "scan_code", None),
            event_type=getattr(event, "event_type", "down"),
        )

    def resolve_stem(self, event: KeyEventSnapshot | keyboard.KeyboardEvent) -> str | None:
        name = normalize_name(event.name)

        if name in {"fn", "function", "fn lock", "function lock"}:
            return UNKNOWN_STEM if UNKNOWN_STEM in self.sound_files else None

        if name in KEY_NAME_OVERRIDES:
            return KEY_NAME_OVERRIDES[name]

        scan_code = getattr(event, "scan_code", None)
        if isinstance(scan_code, int):
            if 0 <= scan_code <= 0xFF:
                direct = f"{scan_code:02x}"
                if direct in self.sound_files:
                    return direct
            folded = f"{scan_code & 0xFF:02x}"
            if folded in self.sound_files:
                return folded

        if name in KEY_NAME_FALLBACKS:
            return KEY_NAME_FALLBACKS[name]

        return UNKNOWN_STEM if UNKNOWN_STEM in self.sound_files else None

    def play_for_event(self, event: KeyEventSnapshot | keyboard.KeyboardEvent) -> None:
        if not self.enabled or not self.mixer_ready:
            return

        stem = self.resolve_stem(event)
        if not stem:
            return

        sound_type = "press" if event.event_type == "down" else "release"
        primary_path = self.sound_files.get(stem, {}).get(sound_type)
        fallback_path = self.sound_files.get(UNKNOWN_STEM, {}).get(sound_type)
        candidate_paths = [path for path in (primary_path, fallback_path) if path is not None]

        for sound_path in dict.fromkeys(candidate_paths):
            if self._play_sound_path(sound_path):
                return

    def load_settings(self) -> None:
        data: dict[str, object] = {}
        loaded_path: Path | None = None
        for path in iter_config_paths(self.config_path):
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                loaded_path = path
                break
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                continue

        if loaded_path is not None:
            self.config_path = loaded_path

        try:
            self.volume = clamp(float(data.get("volume", self.volume)))
        except (TypeError, ValueError):
            self.volume = clamp(self.volume)
        self.enabled = bool(data.get("enabled", self.enabled))
        self.language = normalize_language(data.get("language", self.language))
        stored_hotkeys = data.get("hotkeys", {})
        if isinstance(stored_hotkeys, dict):
            merged = dict(DEFAULT_HOTKEYS)
            for action in DEFAULT_HOTKEYS:
                normalized = normalize_hotkey(stored_hotkeys.get(action))
                if normalized is not None:
                    try:
                        keyboard.parse_hotkey(normalized)
                    except Exception:
                        continue
                    merged[action] = normalized
            self.hotkeys = merged

    def save_settings(self) -> Path | None:
        payload = {
            "volume": round(self.volume, 2),
            "enabled": self.enabled,
            "language": self.language,
            "hotkeys": self.hotkeys,
            "version": APP_VERSION,
        }
        serialized = json.dumps(payload, indent=2)
        errors: list[str] = []

        for config_path in iter_config_paths(self.config_path):
            try:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(serialized, encoding="utf-8")
            except OSError as exc:
                errors.append(f"{config_path}: {exc}")
                continue

            self.config_path = config_path
            self.last_config_error = None
            return config_path

        self.last_config_error = "; ".join(errors) if errors else "Unable to persist settings."
        return None

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        self.save_settings()

    def toggle_enabled(self) -> bool:
        self.enabled = not self.enabled
        self.save_settings()
        return self.enabled

    def set_volume(self, volume: float) -> float:
        self.volume = clamp(volume)
        self.save_settings()
        return self.volume

    def adjust_volume(self, delta: float) -> float:
        return self.set_volume(self.volume + delta)

    def set_hotkeys(self, hotkeys: dict[str, str]) -> None:
        self.hotkeys = dict(hotkeys)
        self.save_settings()

    def set_language(self, language: str) -> None:
        self.language = normalize_language(language)
        self.save_settings()

    def handle_key_event(self, event: keyboard.KeyboardEvent) -> None:
        pressed_key = (getattr(event, "scan_code", None), normalize_name(event.name), "down")
        should_enqueue_audio = False

        if event.event_type == "down":
            if pressed_key in self.pressed_keys:
                return
            self.pressed_keys.add(pressed_key)
            should_enqueue_audio = True
        elif event.event_type == "up":
            # Ignore orphaned releases for audio so startup and focus changes do not create phantom clicks.
            should_enqueue_audio = pressed_key in self.pressed_keys
            self.pressed_keys.discard(pressed_key)

        snapshot = self._snapshot_from_event(event)
        self._emit_event(snapshot)
        if should_enqueue_audio:
            self.audio_queue.put(snapshot)

    def shutdown(self) -> None:
        keyboard.unhook_all()
        keyboard.clear_all_hotkeys()
        self.worker_stop.set()
        self.audio_queue.put(None)
        if self.audio_worker.is_alive():
            self.audio_worker.join(timeout=1)
        if self.mixer_ready:
            pygame.mixer.quit()


class BucklespringApp:
    def __init__(self) -> None:
        self.engine = SoundEngine()
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.configure(bg=BACKGROUND_LAYER_BOTTOM)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.root.bind("<Unmap>", self._on_unmap)
        self.root.geometry("980x780")
        self.root.minsize(940, 740)

        icon_path = resolve_icon_path()
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except tk.TclError:
                pass

        self.status_var = tk.StringVar()
        self.substatus_var = tk.StringVar()
        self.volume_label_var = tk.StringVar()
        self.hotkey_summary_var = tk.StringVar()
        self.language_var = tk.StringVar(value=self.engine.language)
        self.hotkey_feedback_key = "hotkeys_persisted"
        self.hotkey_feedback_kwargs = {"config_name": self.engine.config_path.name}
        self.hotkey_feedback_color = TEXT_MUTED
        self.hotkey_feedback_var = tk.StringVar(value=self.tr(self.hotkey_feedback_key, **self.hotkey_feedback_kwargs))
        self.version_var = tk.StringVar(value=self.tr("version_chip", version=APP_VERSION))
        self.signature_var = tk.StringVar(value=self.tr("build_signature"))
        self.volume_var = tk.IntVar(value=int(round(self.engine.volume * 100)))
        self.hotkey_entry_vars = {
            action: tk.StringVar(value=format_hotkey(self.engine.hotkeys[action]))
            for action, _label, _description, _default in HOTKEY_FIELDS
        }
        self.localized_panels: list[dict[str, object]] = []
        self.hotkey_label_widgets: dict[str, tk.Label] = {}
        self.hotkey_description_widgets: dict[str, tk.Label] = {}
        self.hotkey_callbacks = {
            "toggle_enabled": self._hotkey_toggle_enabled,
            "volume_up": self._hotkey_volume_up,
            "volume_down": self._hotkey_volume_down,
            "hide_window": self._hotkey_hide_window,
            "exit_application": self._hotkey_exit,
        }
        self.scanline_y = 0
        self.background_after_id: str | None = None
        self.diagnostic_events: queue.Queue[KeyEventSnapshot] = queue.Queue()
        self.fn_capture_window: tk.Toplevel | None = None
        self.fn_capture_text: scrolledtext.ScrolledText | None = None
        self.fn_capture_heading_label: tk.Label | None = None
        self.fn_capture_description_label: tk.Label | None = None
        self.fn_capture_clear_button: tk.Button | None = None
        self.fn_capture_copy_button: tk.Button | None = None
        self.fn_capture_close_button: tk.Button | None = None
        self.fn_capture_status_key = "fn_capture_status_intro"
        self.fn_capture_status_kwargs: dict[str, object] = {}
        self.fn_capture_status_var = tk.StringVar(value=self.tr(self.fn_capture_status_key))
        self.fn_capture_samples = 0

        self.tray_icon = pystray.Icon(
            APP_NAME,
            self.load_icon_image(),
            TRAY_TITLE,
            menu=pystray.Menu(
                pystray.MenuItem(lambda item: self.tr("tray_menu_show_window"), self._tray_show_window, default=True),
                pystray.MenuItem(lambda item: self.tr("tray_menu_sound_active"), self._tray_toggle_enabled, checked=lambda item: self.engine.enabled),
                pystray.MenuItem(lambda item: self.tr("tray_menu_exit"), self._tray_exit),
            ),
        )

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.background = tk.Canvas(self.root, bd=0, highlightthickness=0, relief="flat", bg=BACKGROUND_LAYER_BOTTOM)
        self.background.grid(row=0, column=0, sticky="nsew")
        self.surface = tk.Frame(self.root, bg=BACKGROUND_LAYER_TOP)
        self.surface.place(relx=0.5, rely=0.5, relwidth=0.94, relheight=0.92, anchor="center")
        self.root.bind("<Configure>", self._on_root_configure)

        self.engine.add_event_observer(self._queue_diagnostic_event)
        self._build_ui()
        self._build_menu()
        self._bind_menu_shortcuts()
        self._register_keyboard_hooks()
        self._apply_localized_text()
        self.refresh_ui()
        self._draw_background()
        self._animate_background()
        self._drain_diagnostic_queue()

    def tr(self, key: str, **kwargs: object) -> str:
        translations = TRANSLATIONS.get(self.engine.language, TRANSLATIONS[DEFAULT_LANGUAGE])
        fallback = TRANSLATIONS[DEFAULT_LANGUAGE]
        template = translations.get(key, fallback.get(key, key))
        return template.format(**kwargs)

    def hotkey_label(self, action: str) -> str:
        translations = HOTKEY_TRANSLATIONS.get(self.engine.language, HOTKEY_TRANSLATIONS[DEFAULT_LANGUAGE])
        return translations.get(action, {}).get("label", HOTKEY_LABELS[action])

    def hotkey_description(self, action: str) -> str:
        translations = HOTKEY_TRANSLATIONS.get(self.engine.language, HOTKEY_TRANSLATIONS[DEFAULT_LANGUAGE])
        return translations.get(action, {}).get("description", HOTKEY_DESCRIPTIONS[action])

    def _set_hotkey_feedback(self, key: str, *, color: str, **kwargs: object) -> None:
        self.hotkey_feedback_key = key
        self.hotkey_feedback_kwargs = dict(kwargs)
        self.hotkey_feedback_color = color
        self.hotkey_feedback_var.set(self.tr(key, **kwargs))
        if hasattr(self, "hotkey_feedback_label"):
            self.hotkey_feedback_label.configure(fg=color)

    def _set_fn_capture_status(self, key: str, **kwargs: object) -> None:
        self.fn_capture_status_key = key
        self.fn_capture_status_kwargs = dict(kwargs)
        self.fn_capture_status_var.set(self.tr(key, **kwargs))

    def _apply_localized_text(self) -> None:
        self.version_var.set(self.tr("version_chip", version=APP_VERSION))
        self.signature_var.set(self.tr("build_signature"))
        for panel in self.localized_panels:
            panel["title_label"].configure(text=self.tr(str(panel["title_key"])))
            panel["subtitle_label"].configure(text=self.tr(str(panel["subtitle_key"])))

        self.hero_tagline_label.configure(text=self.tr("hero_tagline"))
        self.hero_tray_button.configure(text=self.tr("button_send_to_tray"))
        self.hero_exit_button.configure(text=self.tr("button_exit_application"))
        self.hide_button.configure(text=self.tr("button_minimize_to_tray"))
        self.exit_button.configure(text=self.tr("button_exit_session"))
        self.command_keys_label.configure(text=self.tr("section_command_keys"))
        self.config_path_label.configure(text=self.tr("config_saved_in", config_name=self.engine.config_path.name))
        for action, widget in self.hotkey_label_widgets.items():
            widget.configure(text=self.hotkey_label(action))
        for action, widget in self.hotkey_description_widgets.items():
            widget.configure(text=self.hotkey_description(action))
        self.hotkey_apply_button.configure(text=self.tr("button_apply_hotkeys"))
        self.hotkey_reset_button.configure(text=self.tr("button_reset_defaults"))
        self.fn_lab_button.configure(text=self.tr("button_fn_lab"))
        self.about_button.configure(text=self.tr("button_about"))
        self.output_hint_label.configure(text=self.tr("output_hint"))
        self.decrease_button.configure(text=self.tr("button_decrease_volume"))
        self.increase_button.configure(text=self.tr("button_increase_volume"))
        self._set_hotkey_feedback(self.hotkey_feedback_key, color=self.hotkey_feedback_color, **self.hotkey_feedback_kwargs)
        self._set_fn_capture_status(self.fn_capture_status_key, **self.fn_capture_status_kwargs)
        self._refresh_fn_capture_window_texts()
        self._update_menu_labels()

    def _build_ui(self) -> None:
        self.surface.grid_rowconfigure(0, weight=0)
        self.surface.grid_rowconfigure(1, weight=1)
        self.surface.grid_columnconfigure(0, weight=1)
        self.surface.grid_columnconfigure(1, weight=1)

        hero = self._create_panel(
            self.surface,
            row=0,
            column=0,
            columnspan=2,
            title_key="panel_engine_title",
            subtitle_key="panel_engine_subtitle",
        )
        controls = self._create_panel(
            self.surface,
            row=1,
            column=0,
            title_key="panel_controls_title",
            subtitle_key="panel_controls_subtitle",
        )
        output = self._create_panel(
            self.surface,
            row=1,
            column=1,
            title_key="panel_output_title",
            subtitle_key="panel_output_subtitle",
        )
        self.localized_panels = [hero, controls, output]

        hero_body = hero["body"]
        hero_body.grid_columnconfigure(0, weight=2)
        hero_body.grid_columnconfigure(1, weight=1)
        hero_body.grid_rowconfigure(0, weight=0)

        left_hero = tk.Frame(hero_body, bg=PANEL_ALT_COLOR)
        left_hero.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        right_hero = tk.Frame(hero_body, bg=PANEL_ALT_COLOR)
        right_hero.grid(row=0, column=1, sticky="ne")

        tk.Label(
            left_hero,
            text=APP_NAME.upper(),
            bg=PANEL_ALT_COLOR,
            fg=TEXT_PRIMARY,
            font=("Bahnschrift SemiCondensed", 28, "bold"),
            anchor="w",
        ).pack(anchor="w")
        self.hero_tagline_label = tk.Label(
            left_hero,
            text=self.tr("hero_tagline"),
            bg=PANEL_ALT_COLOR,
            fg=TEXT_MUTED,
            font=("Consolas", 11),
            anchor="w",
        )
        self.hero_tagline_label.pack(anchor="w", pady=(4, 12))
        tk.Label(
            left_hero,
            textvariable=self.substatus_var,
            bg=PANEL_ALT_COLOR,
            fg=ACCENT_CYAN,
            font=("Consolas", 10),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            left_hero,
            textvariable=self.signature_var,
            bg=PANEL_ALT_COLOR,
            fg=TEXT_MUTED,
            font=("Consolas", 9),
            anchor="w",
        ).pack(anchor="w", pady=(10, 0))

        self.status_badge = tk.Label(
            right_hero,
            text="ACTIVE",
            bg=ACCENT_GREEN,
            fg="#041015",
            font=("Bahnschrift SemiBold", 16, "bold"),
            padx=16,
            pady=10,
        )
        self.status_badge.pack(anchor="e")
        self.version_chip = tk.Label(
            right_hero,
            textvariable=self.version_var,
            bg="#0f3542",
            fg=ACCENT_CYAN,
            font=("Consolas", 11, "bold"),
            padx=12,
            pady=6,
        )
        self.version_chip.pack(anchor="e", pady=(14, 12))
        self.hero_tray_button = self._make_action_button(right_hero, self.tr("button_send_to_tray"), self.hide_window, "#0a3340", ACCENT_CYAN)
        self.hero_tray_button.pack(anchor="e", fill="x", pady=(0, 12))
        self.hero_exit_button = self._make_action_button(right_hero, self.tr("button_exit_application"), self.exit_application, "#31151a", ACCENT_RED)
        self.hero_exit_button.pack(anchor="e", fill="x", pady=(0, 12))
        self.health_stack = tk.Frame(right_hero, bg=PANEL_ALT_COLOR)
        self.health_stack.pack(anchor="e", fill="x")
        self.health_chips: list[tk.Label] = []
        for label in ("HOOK LIVE", "TRAY READY", "ASYNC AUDIO"):
            chip = tk.Label(
                self.health_stack,
                text=label,
                bg="#0b3038",
                fg=TEXT_PRIMARY,
                font=("Consolas", 9),
                padx=10,
                pady=4,
            )
            chip.pack(anchor="e", pady=3)
            self.health_chips.append(chip)

        controls_body = controls["body"]
        self.toggle_button = tk.Button(
            controls_body,
            text=self.tr("toggle_deactivate"),
            command=self.toggle_enabled,
            bg="#114955",
            fg=TEXT_PRIMARY,
            activebackground="#15616e",
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Bahnschrift SemiBold", 15, "bold"),
            padx=16,
            pady=14,
        )
        self.toggle_button.pack(fill="x")

        self.status_label = tk.Label(
            controls_body,
            textvariable=self.status_var,
            bg=PANEL_COLOR,
            fg=TEXT_PRIMARY,
            justify="left",
            anchor="w",
            font=("Segoe UI Semibold", 11),
            wraplength=330,
        )
        self.status_label.pack(fill="x", pady=(14, 4))

        self.controls_hint = tk.Label(
            controls_body,
            textvariable=self.hotkey_summary_var,
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            justify="left",
            anchor="w",
            font=("Segoe UI", 10),
            wraplength=330,
        )
        self.controls_hint.pack(fill="x", pady=(0, 14))

        command_row = tk.Frame(controls_body, bg=PANEL_COLOR)
        command_row.pack(fill="x")
        self.hide_button = self._make_action_button(command_row, self.tr("button_minimize_to_tray"), self.hide_window, "#0a3340", ACCENT_CYAN)
        self.hide_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.exit_button = self._make_action_button(command_row, self.tr("button_exit_session"), self.exit_application, "#31151a", ACCENT_RED)
        self.exit_button.pack(side="left", expand=True, fill="x", padx=(6, 0))

        hotkey_panel = tk.Frame(controls_body, bg=PANEL_COLOR)
        hotkey_panel.pack(fill="x", pady=(18, 0))
        self.command_keys_label = tk.Label(
            hotkey_panel,
            text=self.tr("section_command_keys"),
            bg=PANEL_COLOR,
            fg=ACCENT_CYAN,
            font=("Bahnschrift SemiBold", 11, "bold"),
            anchor="w",
        )
        self.command_keys_label.pack(anchor="w")
        self.config_path_label = tk.Label(
            hotkey_panel,
            text=self.tr("config_saved_in", config_name=self.engine.config_path.name),
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            font=("Consolas", 9),
            anchor="w",
        )
        self.config_path_label.pack(anchor="w", pady=(3, 10))

        hotkey_grid = tk.Frame(hotkey_panel, bg=PANEL_COLOR)
        hotkey_grid.pack(fill="x")
        hotkey_grid.grid_columnconfigure(0, weight=0)
        hotkey_grid.grid_columnconfigure(1, weight=1)
        hotkey_grid.grid_columnconfigure(2, weight=0)

        self.hotkey_entries: dict[str, tk.Entry] = {}
        for row, (action, label, description, _default) in enumerate(HOTKEY_FIELDS):
            label_widget = tk.Label(
                hotkey_grid,
                text=self.hotkey_label(action),
                bg=PANEL_COLOR,
                fg=TEXT_PRIMARY,
                font=("Bahnschrift SemiBold", 10, "bold"),
                anchor="w",
            )
            label_widget.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            self.hotkey_label_widgets[action] = label_widget
            entry = tk.Entry(
                hotkey_grid,
                textvariable=self.hotkey_entry_vars[action],
                bg="#09161c",
                fg=ACCENT_CYAN,
                insertbackground=ACCENT_CYAN,
                relief="flat",
                bd=0,
                font=("Consolas", 11),
                width=18,
            )
            entry.grid(row=row, column=1, sticky="ew", pady=5)
            self.hotkey_entries[action] = entry
            description_widget = tk.Label(
                hotkey_grid,
                text=self.hotkey_description(action),
                bg=PANEL_COLOR,
                fg=TEXT_MUTED,
                font=("Consolas", 8),
                anchor="w",
                justify="left",
                wraplength=150,
            )
            description_widget.grid(row=row, column=2, sticky="w", padx=(10, 0), pady=5)
            self.hotkey_description_widgets[action] = description_widget

        hotkey_actions = tk.Frame(hotkey_panel, bg=PANEL_COLOR)
        hotkey_actions.pack(fill="x", pady=(12, 0))
        self.hotkey_apply_button = self._make_action_button(hotkey_actions, self.tr("button_apply_hotkeys"), self.apply_hotkeys_from_gui, "#12362f", ACCENT_GREEN)
        self.hotkey_apply_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.hotkey_reset_button = self._make_action_button(hotkey_actions, self.tr("button_reset_defaults"), self.reset_hotkeys_to_defaults, "#2e2413", ACCENT_ORANGE)
        self.hotkey_reset_button.pack(side="left", expand=True, fill="x", padx=(6, 0))
        self.hotkey_feedback_label = tk.Label(
            hotkey_panel,
            textvariable=self.hotkey_feedback_var,
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            justify="left",
            anchor="w",
            font=("Consolas", 9),
            wraplength=330,
        )
        self.hotkey_feedback_label.pack(fill="x", pady=(10, 0))

        lab_actions = tk.Frame(hotkey_panel, bg=PANEL_COLOR)
        lab_actions.pack(fill="x", pady=(12, 0))
        self.fn_lab_button = self._make_action_button(lab_actions, self.tr("button_fn_lab"), self.open_fn_capture_window, "#12303c", ACCENT_CYAN)
        self.fn_lab_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.about_button = self._make_action_button(lab_actions, self.tr("button_about"), self.show_about_dialog, "#14242c", TEXT_PRIMARY)
        self.about_button.pack(side="left", expand=True, fill="x", padx=(6, 0))

        output_body = output["body"]
        visuals = tk.Frame(output_body, bg=PANEL_COLOR)
        visuals.pack(fill="x")
        visuals.grid_columnconfigure(0, weight=0)
        visuals.grid_columnconfigure(1, weight=1)

        self.volume_dial_canvas = tk.Canvas(
            visuals,
            bg=PANEL_COLOR,
            bd=0,
            highlightthickness=0,
            width=220,
            height=220,
            relief="flat",
            cursor="hand2",
        )
        self.volume_dial_canvas.grid(row=0, column=0, sticky="nw", padx=(0, 18))
        self.volume_dial_canvas.bind("<Button-1>", self._on_volume_dial_interact)
        self.volume_dial_canvas.bind("<B1-Motion>", self._on_volume_dial_interact)

        output_status = tk.Frame(visuals, bg=PANEL_COLOR)
        output_status.grid(row=0, column=1, sticky="nsew")
        self.volume_display = tk.Label(
            output_status,
            textvariable=self.volume_label_var,
            bg=PANEL_COLOR,
            fg=TEXT_PRIMARY,
            font=("Bahnschrift SemiBold", 18, "bold"),
            anchor="w",
        )
        self.volume_display.pack(fill="x")
        self.output_hint_label = tk.Label(
            output_status,
            text=self.tr("output_hint"),
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=280,
        )
        self.output_hint_label.pack(fill="x", pady=(6, 12))
        self.output_state_label = tk.Label(
            output_status,
            text=self.tr("output_state_active"),
            bg="#0b3038",
            fg=ACCENT_CYAN,
            font=("Consolas", 10, "bold"),
            padx=12,
            pady=8,
            anchor="w",
        )
        self.output_state_label.pack(fill="x", pady=(0, 10))
        self.output_hotkey_label = tk.Label(
            output_status,
            text="",
            bg="#0b2430",
            fg=TEXT_PRIMARY,
            font=("Consolas", 10),
            justify="left",
            anchor="w",
            padx=12,
            pady=10,
        )
        self.output_hotkey_label.pack(fill="x")

        self.volume_canvas = tk.Canvas(
            output_body,
            bg=PANEL_COLOR,
            bd=0,
            highlightthickness=0,
            height=150,
            relief="flat",
            cursor="hand2",
        )
        self.volume_canvas.pack(fill="both", expand=True, pady=(14, 10))
        self.volume_canvas.bind("<Button-1>", self._on_volume_canvas_click)

        output_controls = tk.Frame(output_body, bg=PANEL_COLOR)
        output_controls.pack(fill="x")
        self.decrease_button = self._make_action_button(output_controls, self.tr("button_decrease_volume"), lambda: self._set_volume_and_refresh(self.engine.adjust_volume(-VOLUME_STEP)), "#102832", ACCENT_CYAN)
        self.decrease_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.increase_button = self._make_action_button(output_controls, self.tr("button_increase_volume"), lambda: self._set_volume_and_refresh(self.engine.adjust_volume(VOLUME_STEP)), "#12362f", ACCENT_GREEN)
        self.increase_button.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _build_menu(self) -> None:
        self.menu_bar = tk.Menu(self.root)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.file_menu.add_command(label=self.tr("menu_file_send_to_tray"), command=self.hide_window, accelerator="")
        self.file_menu.add_command(label=self.tr("menu_file_show_window"), command=self.show_window, accelerator="")
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.tr("menu_file_exit"), command=self.exit_application, accelerator="")
        self.menu_bar.add_cascade(label=self.tr("menu_file"), menu=self.file_menu)

        self.settings_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.settings_menu.add_command(label=self.tr("menu_settings_apply_hotkeys"), command=self.apply_hotkeys_from_gui, accelerator="Ctrl+Enter")
        self.settings_menu.add_command(label=self.tr("menu_settings_reset_hotkeys"), command=self.reset_hotkeys_to_defaults, accelerator="Ctrl+Shift+R")
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self.tr("menu_settings_fn_lab"), command=self.open_fn_capture_window, accelerator="Ctrl+Shift+F")
        self.menu_bar.add_cascade(label=self.tr("menu_settings"), menu=self.settings_menu)

        self.language_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.language_menu.add_radiobutton(label=self.tr("language_option_en"), variable=self.language_var, value="en", command=lambda: self.change_language("en"))
        self.language_menu.add_radiobutton(label=self.tr("language_option_es"), variable=self.language_var, value="es", command=lambda: self.change_language("es"))
        self.menu_bar.add_cascade(label=self.tr("menu_language"), menu=self.language_menu)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.help_menu.add_command(label=self.tr("menu_help_about", version=APP_VERSION), command=self.show_about_dialog, accelerator="F1")
        self.menu_bar.add_cascade(label=self.tr("menu_help"), menu=self.help_menu)

        self.root.configure(menu=self.menu_bar)
        self._update_menu_labels()

    def _bind_menu_shortcuts(self) -> None:
        self.root.bind_all("<F1>", self._on_about_shortcut)
        self.root.bind_all("<Control-Return>", self._on_apply_hotkeys_shortcut)
        self.root.bind_all("<Control-Shift-R>", self._on_reset_hotkeys_shortcut)
        self.root.bind_all("<Control-Shift-F>", self._on_fn_capture_shortcut)
        self.root.bind_all("<Control-Shift-W>", self._on_show_window_shortcut)

    def change_language(self, language: str) -> None:
        normalized = normalize_language(language)
        self.language_var.set(normalized)
        if normalized != self.engine.language:
            self.engine.set_language(normalized)
        self._build_menu()
        self._apply_localized_text()
        self.refresh_ui()

    def _update_menu_labels(self) -> None:
        if not hasattr(self, "file_menu"):
            return

        self.file_menu.entryconfigure(0, label=self.tr("menu_file_send_to_tray"), accelerator=format_hotkey(self.engine.hotkeys["hide_window"]))
        self.file_menu.entryconfigure(1, label=self.tr("menu_file_show_window"), accelerator="Ctrl + Shift + W")
        self.file_menu.entryconfigure(3, label=self.tr("menu_file_exit"), accelerator=format_hotkey(self.engine.hotkeys["exit_application"]))

        self.settings_menu.entryconfigure(0, label=self.tr("menu_settings_apply_hotkeys"), accelerator="Ctrl + Enter")
        self.settings_menu.entryconfigure(1, label=self.tr("menu_settings_reset_hotkeys"), accelerator="Ctrl + Shift + R")
        self.settings_menu.entryconfigure(3, label=self.tr("menu_settings_fn_lab"), accelerator="Ctrl + Shift + F")

        self.language_menu.entryconfigure(0, label=self.tr("language_option_en"))
        self.language_menu.entryconfigure(1, label=self.tr("language_option_es"))
        self.help_menu.entryconfigure(0, label=self.tr("menu_help_about", version=APP_VERSION), accelerator="F1")


    def _create_panel(
        self,
        parent: tk.Misc,
        *,
        row: int,
        column: int,
        title_key: str,
        subtitle_key: str,
        columnspan: int = 1,
    ) -> dict[str, tk.Frame]:
        panel = tk.Frame(
            parent,
            bg=PANEL_COLOR,
            bd=0,
            highlightbackground=GRID_LINE,
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        panel.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=24, pady=(22 if row == 0 else 0, 18))
        parent.grid_columnconfigure(column, weight=1)
        if columnspan == 2:
            parent.grid_columnconfigure(column + 1, weight=1)
        if row == 1:
            parent.grid_rowconfigure(row, weight=1)

        header = tk.Frame(panel, bg=PANEL_COLOR)
        header.pack(fill="x", pady=(0, 14))
        title_label = tk.Label(
            header,
            text=self.tr(title_key),
            bg=PANEL_COLOR,
            fg=ACCENT_CYAN,
            font=("Bahnschrift SemiBold", 10, "bold"),
            anchor="w",
        )
        title_label.pack(side="left")
        subtitle_label = tk.Label(
            header,
            text=self.tr(subtitle_key),
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            font=("Consolas", 9),
            anchor="e",
        )
        subtitle_label.pack(side="right")

        body = tk.Frame(panel, bg=PANEL_COLOR)
        body.pack(fill="both", expand=True)
        return {
            "panel": panel,
            "body": body,
            "title_label": title_label,
            "subtitle_label": subtitle_label,
            "title_key": title_key,
            "subtitle_key": subtitle_key,
        }

    def _make_action_button(self, parent: tk.Misc, text: str, command: object, bg: str, fg: str) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=fg,
            activeforeground="#021014",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Bahnschrift SemiBold", 10, "bold"),
            padx=12,
            pady=11,
        )
        return button

    def _register_keyboard_hooks(self) -> None:
        keyboard.hook(self.engine.handle_key_event)
        try:
            self._register_hotkeys(self.engine.hotkeys)
        except Exception:
            self.engine.hotkeys = dict(DEFAULT_HOTKEYS)
            self._register_hotkeys(self.engine.hotkeys)
            self.engine.save_settings()

    def _register_hotkeys(self, hotkeys: dict[str, str]) -> None:
        keyboard.clear_all_hotkeys()
        seen: set[str] = set()
        for action, _label, _description, _default in HOTKEY_FIELDS:
            hotkey = normalize_hotkey(hotkeys.get(action))
            if hotkey is None:
                raise ValueError(self.tr("hotkey_empty", label=self.hotkey_label(action)))
            if hotkey in seen:
                raise ValueError(self.tr("hotkey_duplicate", hotkey=format_hotkey(hotkey)))
            keyboard.parse_hotkey(hotkey)
            keyboard.add_hotkey(hotkey, self.hotkey_callbacks[action])
            seen.add(hotkey)

    def _apply_hotkeys(self, hotkeys: dict[str, str], *, persist: bool) -> None:
        previous = dict(self.engine.hotkeys)
        try:
            self._register_hotkeys(hotkeys)
        except Exception:
            self._register_hotkeys(previous)
            raise

        if persist:
            self.engine.set_hotkeys(hotkeys)
        else:
            self.engine.hotkeys = dict(hotkeys)

    def _queue_diagnostic_event(self, snapshot: KeyEventSnapshot) -> None:
        if self.fn_capture_window is None:
            return
        self.diagnostic_events.put(snapshot)

    def _drain_diagnostic_queue(self) -> None:
        while True:
            try:
                snapshot = self.diagnostic_events.get_nowait()
            except queue.Empty:
                break
            self._append_diagnostic_snapshot(snapshot)

        self.root.after(80, self._drain_diagnostic_queue)

    def _append_diagnostic_snapshot(self, snapshot: KeyEventSnapshot) -> None:
        if self.fn_capture_text is None or self.fn_capture_window is None:
            return

        self.fn_capture_samples += 1
        scan_code = "--" if snapshot.scan_code is None else str(snapshot.scan_code)
        key_name = snapshot.name or self.tr("fn_missing_name")
        line = (
            f"[{self.fn_capture_samples:03d}] "
            f"{self.tr('diag_field_type')}={snapshot.event_type:<5} "
            f"{self.tr('diag_field_scan')}={scan_code:<4} "
            f"{self.tr('diag_field_name')}={key_name}\n"
        )
        self.fn_capture_text.insert("end", line)
        self.fn_capture_text.see("end")

        if normalize_name(snapshot.name) in {"fn", "function", "fn lock", "function lock"}:
            self._set_fn_capture_status("fn_capture_status_detected")
        else:
            self._set_fn_capture_status("fn_capture_status_hidden")

    def open_fn_capture_window(self) -> None:
        if self.fn_capture_window is not None and self.fn_capture_window.winfo_exists():
            self.fn_capture_window.deiconify()
            self.fn_capture_window.lift()
            self.fn_capture_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        window.title(self.tr("fn_capture_window_title", app_name=APP_NAME, version=APP_VERSION))
        window.configure(bg=BACKGROUND_LAYER_TOP)
        window.geometry("760x420")
        window.minsize(680, 360)
        window.transient(self.root)
        window.protocol("WM_DELETE_WINDOW", self.close_fn_capture_window)
        self.fn_capture_window = window
        self.fn_capture_text = None
        self.fn_capture_samples = 0

        shell = tk.Frame(window, bg=PANEL_COLOR, padx=18, pady=16, highlightbackground=GRID_LINE, highlightthickness=1)
        shell.pack(fill="both", expand=True, padx=20, pady=20)

        self.fn_capture_heading_label = tk.Label(
            shell,
            text=self.tr("fn_capture_heading"),
            bg=PANEL_COLOR,
            fg=ACCENT_CYAN,
            font=("Bahnschrift SemiBold", 15, "bold"),
            anchor="w",
        )
        self.fn_capture_heading_label.pack(anchor="w")
        self.fn_capture_description_label = tk.Label(
            shell,
            text=self.tr("fn_capture_description"),
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            font=("Segoe UI", 10),
            justify="left",
            wraplength=680,
            anchor="w",
        )
        self.fn_capture_description_label.pack(fill="x", pady=(6, 10))

        status = tk.Label(
            shell,
            textvariable=self.fn_capture_status_var,
            bg="#0b2430",
            fg=TEXT_PRIMARY,
            font=("Consolas", 10),
            justify="left",
            anchor="w",
            padx=12,
            pady=10,
        )
        status.pack(fill="x", pady=(0, 12))

        self.fn_capture_text = scrolledtext.ScrolledText(
            shell,
            bg="#07141a",
            fg=ACCENT_CYAN,
            insertbackground=ACCENT_CYAN,
            relief="flat",
            bd=0,
            font=("Consolas", 10),
            wrap="none",
        )
        self.fn_capture_text.pack(fill="both", expand=True)

        action_row = tk.Frame(shell, bg=PANEL_COLOR)
        action_row.pack(fill="x", pady=(12, 0))
        self.fn_capture_clear_button = self._make_action_button(action_row, self.tr("fn_capture_clear"), self.clear_fn_capture_log, "#102832", ACCENT_CYAN)
        self.fn_capture_clear_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.fn_capture_copy_button = self._make_action_button(action_row, self.tr("fn_capture_copy"), self.copy_fn_capture_log, "#12362f", ACCENT_GREEN)
        self.fn_capture_copy_button.pack(side="left", expand=True, fill="x", padx=6)
        self.fn_capture_close_button = self._make_action_button(action_row, self.tr("fn_capture_close"), self.close_fn_capture_window, "#31151a", ACCENT_RED)
        self.fn_capture_close_button.pack(side="left", expand=True, fill="x", padx=(6, 0))

        self._set_fn_capture_status("fn_capture_status_no_event")
        self.clear_fn_capture_log()

    def _refresh_fn_capture_window_texts(self) -> None:
        if self.fn_capture_window is None or not self.fn_capture_window.winfo_exists():
            return
        self.fn_capture_window.title(self.tr("fn_capture_window_title", app_name=APP_NAME, version=APP_VERSION))
        if self.fn_capture_heading_label is not None:
            self.fn_capture_heading_label.configure(text=self.tr("fn_capture_heading"))
        if self.fn_capture_description_label is not None:
            self.fn_capture_description_label.configure(text=self.tr("fn_capture_description"))
        if self.fn_capture_clear_button is not None:
            self.fn_capture_clear_button.configure(text=self.tr("fn_capture_clear"))
        if self.fn_capture_copy_button is not None:
            self.fn_capture_copy_button.configure(text=self.tr("fn_capture_copy"))
        if self.fn_capture_close_button is not None:
            self.fn_capture_close_button.configure(text=self.tr("fn_capture_close"))

    def clear_fn_capture_log(self) -> None:
        self.fn_capture_samples = 0
        if self.fn_capture_text is not None:
            self.fn_capture_text.delete("1.0", "end")
        self._set_fn_capture_status("fn_capture_status_no_event")

    def copy_fn_capture_log(self) -> None:
        if self.fn_capture_text is None:
            return
        content = self.fn_capture_text.get("1.0", "end").strip()
        if not content:
            self._set_fn_capture_status("fn_capture_status_no_entries")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self._set_fn_capture_status("fn_capture_status_copied")

    def close_fn_capture_window(self) -> None:
        if self.fn_capture_window is not None:
            try:
                self.fn_capture_window.destroy()
            except tk.TclError:
                pass
        self.fn_capture_window = None
        self.fn_capture_text = None
        self.fn_capture_heading_label = None
        self.fn_capture_description_label = None
        self.fn_capture_clear_button = None
        self.fn_capture_copy_button = None
        self.fn_capture_close_button = None

    def show_about_dialog(self) -> None:
        messagebox.showinfo(
            title=self.tr("about_title", app_name=APP_NAME),
            message=self.tr(
                "about_message",
                app_name=APP_NAME,
                version=APP_VERSION,
                author=APP_AUTHOR,
                license=APP_LICENSE,
                year=date.today().year,
            ),
            parent=self.root,
        )

    def _on_about_shortcut(self, event: tk.Event) -> str:
        del event
        self.show_about_dialog()
        return "break"

    def _on_apply_hotkeys_shortcut(self, event: tk.Event) -> str:
        del event
        self.apply_hotkeys_from_gui()
        return "break"

    def _on_reset_hotkeys_shortcut(self, event: tk.Event) -> str:
        del event
        self.reset_hotkeys_to_defaults()
        return "break"

    def _on_fn_capture_shortcut(self, event: tk.Event) -> str:
        del event
        self.open_fn_capture_window()
        return "break"

    def _on_show_window_shortcut(self, event: tk.Event) -> str:
        del event
        self.show_window()
        return "break"

    def load_icon_image(self) -> Image.Image:
        icon_path = resolve_icon_path()
        if icon_path.exists():
            try:
                return Image.open(icon_path)
            except OSError:
                pass

        image = Image.new("RGBA", (64, 64), (36, 40, 47, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((10, 18, 54, 46), fill=(232, 233, 237, 255), outline=(90, 96, 104, 255))
        draw.rectangle((14, 22, 50, 42), fill=(62, 66, 76, 255))
        for x in range(16, 48, 8):
            draw.line((x, 24, x, 40), fill=(195, 198, 204, 255), width=1)
        return image

    def _on_unmap(self, _event: tk.Event) -> None:
        if self.root.state() == "iconic":
            self.hide_window()

    def _on_root_configure(self, _event: tk.Event) -> None:
        self._draw_background()
        self._draw_volume_dial()
        self._draw_volume_meter()

    def _draw_background(self) -> None:
        width = max(self.root.winfo_width(), 860)
        height = max(self.root.winfo_height(), 560)
        self.background.delete("bg")

        for band in range(18):
            ratio = band / 17
            red = int(7 + (3 * ratio))
            green = int(22 + (18 * ratio))
            blue = int(29 + (18 * ratio))
            color = f"#{red:02x}{green:02x}{blue:02x}"
            y1 = int((height / 18) * band)
            y2 = int((height / 18) * (band + 1)) + 1
            self.background.create_rectangle(0, y1, width, y2, fill=color, outline=color, tags="bg")

        for x in range(0, width, 42):
            self.background.create_line(x, 0, x, height, fill=GRID_LINE, width=1, tags="bg")
        for y in range(0, height, 42):
            self.background.create_line(0, y, width, y, fill=GRID_LINE, width=1, tags="bg")

        self.background.create_oval(-140, -140, 200, 200, outline="#0f3944", width=2, tags="bg")
        self.background.create_oval(width - 240, height - 210, width + 120, height + 120, outline="#12323e", width=2, tags="bg")
        self.background.create_polygon(
            width - 240,
            0,
            width,
            0,
            width,
            180,
            width - 96,
            120,
            fill="#071b22",
            outline="",
            tags="bg",
        )

    def _animate_background(self) -> None:
        width = max(self.root.winfo_width(), 860)
        height = max(self.root.winfo_height(), 560)
        travel = max(height - 120, 1)
        self.scanline_y = 60 + ((self.scanline_y + 7) % travel)
        self.background.delete("scan")
        self.background.create_rectangle(
            0,
            self.scanline_y - 2,
            width,
            self.scanline_y + 2,
            fill="#0b313c",
            outline="",
            tags="scan",
        )
        self.background.create_line(0, self.scanline_y, width, self.scanline_y, fill=ACCENT_CYAN, width=1, tags="scan")
        self.background.create_line(0, self.scanline_y + 8, width, self.scanline_y + 8, fill="#103341", width=1, tags="scan")
        self.background_after_id = self.root.after(90, self._animate_background)

    def _draw_volume_meter(self) -> None:
        if not hasattr(self, "volume_canvas"):
            return

        canvas = self.volume_canvas
        width = max(canvas.winfo_width(), 320)
        height = max(canvas.winfo_height(), 178)
        canvas.delete("all")

        canvas.create_text(18, 16, text=self.tr("volume_meter_title"), anchor="w", fill=TEXT_MUTED, font=("Consolas", 10))
        canvas.create_text(
            width - 18,
            16,
            text=self.tr("status_word_active") if self.engine.enabled else self.tr("status_word_muted"),
            anchor="e",
            fill=ACCENT_GREEN if self.engine.enabled else ACCENT_ORANGE,
            font=("Consolas", 10, "bold"),
        )

        normalized = (self.engine.volume - MIN_VOLUME) / (MAX_VOLUME - MIN_VOLUME)
        normalized = max(0.0, min(1.0, normalized))
        segments = 14
        active_segments = int(round(normalized * segments))
        left = 22
        right = width - 22
        top = 52
        bottom = height - 42
        gap = 8
        total_gap = gap * (segments - 1)
        segment_width = max((right - left - total_gap) / segments, 8)

        for index in range(segments):
            x1 = left + index * (segment_width + gap)
            x2 = x1 + segment_width
            ratio = (index + 1) / segments
            bar_height = 34 + (ratio * 58)
            y1 = bottom - bar_height
            fill = "#10313a"
            outline = "#143944"
            if index < active_segments:
                fill = ACCENT_GREEN if ratio > 0.72 else ACCENT_CYAN
                outline = fill
                if not self.engine.enabled:
                    fill = ACCENT_ORANGE
                    outline = ACCENT_ORANGE
            canvas.create_rectangle(x1, y1, x2, bottom, fill=fill, outline=outline, width=1)

        canvas.create_line(left, bottom + 10, right, bottom + 10, fill=GRID_LINE, width=2)
        for tick in range(4):
            tick_x = left + ((right - left) / 3) * tick
            canvas.create_line(tick_x, bottom + 10, tick_x, bottom + 18, fill=GRID_LINE, width=1)

        canvas.create_text(left, height - 18, text="00%", anchor="w", fill=TEXT_MUTED, font=("Consolas", 9))
        canvas.create_text(width / 2, height - 18, text=self.tr("volume_meter_footer"), anchor="center", fill=TEXT_MUTED, font=("Consolas", 9))
        canvas.create_text(right, height - 18, text="100%", anchor="e", fill=TEXT_MUTED, font=("Consolas", 9))

    def _draw_volume_dial(self) -> None:
        if not hasattr(self, "volume_dial_canvas"):
            return

        canvas = self.volume_dial_canvas
        width = max(canvas.winfo_width(), 220)
        height = max(canvas.winfo_height(), 220)
        canvas.delete("all")

        cx = width / 2
        cy = height / 2
        outer_radius = min(width, height) / 2 - 18
        inner_radius = outer_radius - 20
        normalized = (self.engine.volume - MIN_VOLUME) / (MAX_VOLUME - MIN_VOLUME)
        normalized = max(0.0, min(1.0, normalized))
        segments = 60

        canvas.create_oval(
            cx - outer_radius - 6,
            cy - outer_radius - 6,
            cx + outer_radius + 6,
            cy + outer_radius + 6,
            outline="#0b2631",
            width=2,
        )

        for index in range(segments):
            ratio = index / max(segments - 1, 1)
            angle_deg = 135 + (ratio * 270)
            radians = math.radians(angle_deg)
            x1 = cx + (math.cos(radians) * inner_radius)
            y1 = cy + (math.sin(radians) * inner_radius)
            x2 = cx + (math.cos(radians) * outer_radius)
            y2 = cy + (math.sin(radians) * outer_radius)

            fill = "#0d2a35"
            if ratio <= normalized + 1e-9:
                fill = ACCENT_GREEN if ratio > 0.7 else ACCENT_CYAN
                if not self.engine.enabled:
                    fill = ACCENT_ORANGE
            canvas.create_line(x1, y1, x2, y2, fill=fill, width=4, capstyle=tk.ROUND)

        knob_angle = math.radians(135 + (normalized * 270))
        knob_radius = (inner_radius + outer_radius) / 2
        knob_x = cx + (math.cos(knob_angle) * knob_radius)
        knob_y = cy + (math.sin(knob_angle) * knob_radius)
        knob_fill = ACCENT_GREEN if self.engine.enabled else ACCENT_ORANGE

        canvas.create_oval(knob_x - 9, knob_y - 9, knob_x + 9, knob_y + 9, fill=knob_fill, outline="#021014", width=2)
        canvas.create_oval(cx - 54, cy - 54, cx + 54, cy + 54, fill="#07141a", outline="#11303b", width=2)
        canvas.create_text(cx, cy - 14, text=f"{int(round(self.engine.volume * 100)):03d}%", fill=TEXT_PRIMARY, font=("Bahnschrift SemiBold", 28, "bold"))
        canvas.create_text(cx, cy + 16, text=self.tr("output_dial_title"), fill=TEXT_MUTED, font=("Consolas", 10))
        canvas.create_text(cx, cy + 36, text=self.tr("status_word_active") if self.engine.enabled else self.tr("status_word_muted"), fill=knob_fill, font=("Consolas", 10, "bold"))
        canvas.create_text(24, height - 20, text="0", fill=TEXT_MUTED, font=("Consolas", 9), anchor="w")
        canvas.create_text(width - 24, height - 20, text="100", fill=TEXT_MUTED, font=("Consolas", 9), anchor="e")

    def _volume_ratio_from_point(self, x: float, y: float, width: int, height: int) -> float:
        cx = width / 2
        cy = height / 2
        angle = (math.degrees(math.atan2(y - cy, x - cx)) + 360) % 360

        if 45 < angle < 135:
            return 0.0 if x < cx else 1.0
        if angle < 135:
            angle += 360
        return max(0.0, min(1.0, (angle - 135) / 270))

    def _on_volume_canvas_click(self, event: tk.Event) -> None:
        canvas = self.volume_canvas
        width = max(canvas.winfo_width(), 320)
        left = 22
        right = width - 22
        ratio = (event.x - left) / max(right - left, 1)
        ratio = max(0.0, min(1.0, ratio))
        self._set_volume_and_refresh(self.engine.set_volume(MIN_VOLUME + ratio * (MAX_VOLUME - MIN_VOLUME)))

    def _on_volume_dial_interact(self, event: tk.Event) -> None:
        canvas = self.volume_dial_canvas
        width = max(canvas.winfo_width(), 220)
        height = max(canvas.winfo_height(), 220)
        ratio = self._volume_ratio_from_point(event.x, event.y, width, height)
        self._set_volume_and_refresh(self.engine.set_volume(MIN_VOLUME + ratio * (MAX_VOLUME - MIN_VOLUME)))

    def refresh_ui(self) -> None:
        status = self.tr("status_word_active") if self.engine.enabled else self.tr("status_word_muted")
        mixer_state = self.tr("mixer_online") if self.engine.mixer_ready else self.tr("mixer_unavailable")
        self.status_var.set(self.tr("status_summary", status=status, mixer=mixer_state, config_name=self.engine.config_path.name))
        self.substatus_var.set(self.tr("substatus_summary"))
        self.version_var.set(self.tr("version_chip", version=APP_VERSION))
        self.signature_var.set(self.tr("build_signature"))
        self.toggle_button.configure(
            text=self.tr("toggle_deactivate") if self.engine.enabled else self.tr("toggle_reactivate"),
            bg="#114955" if self.engine.enabled else "#4f3017",
            activebackground="#15616e" if self.engine.enabled else "#ff9b54",
        )
        self.status_badge.configure(
            text=self.tr("status_word_active") if self.engine.enabled else self.tr("status_word_muted"),
            bg=ACCENT_GREEN if self.engine.enabled else ACCENT_ORANGE,
            fg="#041015",
        )
        chip_specs = (
            (self.tr("health_hook_live") if self.engine.enabled else self.tr("health_hook_idle"), ACCENT_GREEN if self.engine.enabled else ACCENT_ORANGE),
            (self.tr("health_tray_ready"), ACCENT_CYAN),
            (self.tr("health_async_audio"), ACCENT_CYAN),
        )
        for chip, (text, color) in zip(self.health_chips, chip_specs, strict=False):
            chip.configure(text=text, fg=color)
        volume_percent = int(round(self.engine.volume * 100))
        self.volume_var.set(volume_percent)
        self.volume_label_var.set(self.tr("volume_output_level", volume=volume_percent))
        self.output_state_label.configure(
            text=self.tr("output_state_active") if self.engine.enabled else self.tr("output_state_muted"),
            fg=ACCENT_CYAN if self.engine.enabled else ACCENT_ORANGE,
        )
        summary = "  |  ".join(
            f"{format_hotkey(self.engine.hotkeys[action])} {self.hotkey_label(action)}"
            for action, _label, _description, _default in HOTKEY_FIELDS
        )
        self.hotkey_summary_var.set(self.tr("window_tray_hint", summary=summary))
        self.output_hotkey_label.configure(
            text=(
                f"{self.tr('output_tray_label')}  {format_hotkey(self.engine.hotkeys['hide_window'])}\n"
                f"{self.tr('output_exit_label')}  {format_hotkey(self.engine.hotkeys['exit_application'])}"
            )
        )
        self.hotkey_feedback_var.set(self.tr(self.hotkey_feedback_key, **self.hotkey_feedback_kwargs))
        self.tray_icon.title = f"{TRAY_TITLE} - {self.tr('tray_title_active') if self.engine.enabled else self.tr('tray_title_muted')}"
        self.tray_icon.update_menu()
        self._update_menu_labels()
        self._draw_volume_dial()
        self._draw_volume_meter()

    def on_volume_change(self, raw_value: str) -> None:
        try:
            value = float(raw_value) / 100
        except (TypeError, ValueError):
            return
        self.engine.set_volume(value)
        self.refresh_ui()

    def toggle_enabled(self) -> None:
        self.engine.toggle_enabled()
        self.refresh_ui()

    def apply_hotkeys_from_gui(self) -> None:
        candidate: dict[str, str] = {}
        for action, _label, _description, _default in HOTKEY_FIELDS:
            normalized = normalize_hotkey(self.hotkey_entry_vars[action].get())
            if normalized is None:
                self._set_hotkey_feedback("hotkey_requires_valid", color=ACCENT_RED, label=self.hotkey_label(action))
                return
            candidate[action] = normalized

        try:
            self._apply_hotkeys(candidate, persist=True)
        except Exception as exc:
            self._set_hotkey_feedback("hotkeys_apply_error", color=ACCENT_RED, error=str(exc))
            self._sync_hotkey_entries()
            return

        self._set_hotkey_feedback("hotkeys_applied", color=ACCENT_GREEN, config_name=self.engine.config_path.name)
        self._sync_hotkey_entries()
        self.refresh_ui()

    def reset_hotkeys_to_defaults(self) -> None:
        try:
            self._apply_hotkeys(dict(DEFAULT_HOTKEYS), persist=True)
        except Exception as exc:
            self._set_hotkey_feedback("hotkeys_reset_error", color=ACCENT_RED, error=str(exc))
            return

        self._set_hotkey_feedback("hotkeys_reset", color=ACCENT_GREEN)
        self._sync_hotkey_entries()
        self.refresh_ui()

    def _sync_hotkey_entries(self) -> None:
        for action in self.hotkey_entry_vars:
            self.hotkey_entry_vars[action].set(format_hotkey(self.engine.hotkeys[action]))

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self) -> None:
        self.root.withdraw()

    def _tray_show_window(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        del icon, item
        self.root.after(0, self.show_window)

    def _tray_toggle_enabled(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        del icon, item
        self.root.after(0, self.toggle_enabled)

    def _tray_exit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        del icon, item
        self.root.after(0, self.exit_application)

    def _hotkey_toggle_enabled(self) -> None:
        self.root.after(0, self.toggle_enabled)

    def _hotkey_volume_up(self) -> None:
        self.root.after(0, lambda: self._set_volume_and_refresh(self.engine.adjust_volume(VOLUME_STEP)))

    def _hotkey_volume_down(self) -> None:
        self.root.after(0, lambda: self._set_volume_and_refresh(self.engine.adjust_volume(-VOLUME_STEP)))

    def _hotkey_hide_window(self) -> None:
        self.root.after(0, self.hide_window)

    def _hotkey_exit(self) -> None:
        self.root.after(0, self.exit_application)

    def _set_volume_and_refresh(self, value: float) -> None:
        self.engine.volume = value
        self.engine.save_settings()
        self.refresh_ui()

    def start(self) -> None:
        self.tray_icon.run_detached()
        self.root.mainloop()

    def exit_application(self) -> None:
        if self.background_after_id:
            self.root.after_cancel(self.background_after_id)
            self.background_after_id = None
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.engine.shutdown()
        self.root.destroy()


def main() -> int:
    args = parse_args()
    if args.version:
        print(APP_VERSION)
        return 0

    guard = SingleInstanceGuard(MUTEX_NAME)
    if not guard.acquire():
        return 0

    atexit.register(guard.release)

    app = BucklespringApp()
    try:
        app.start()
    finally:
        guard.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
