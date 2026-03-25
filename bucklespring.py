from __future__ import annotations

import argparse
import atexit
import ctypes
import json
import math
import os
import sys
import threading
import tkinter as tk
import warnings
from pathlib import Path

import keyboard
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import pygame
import pystray
from PIL import Image, ImageDraw

from version import APP_NAME, APP_VERSION


DEFAULT_VOLUME = 0.10
MIN_VOLUME = 0.01
MAX_VOLUME = 0.95
VOLUME_STEP = 0.05
CONFIG_FILE = Path.home() / ".keyboard_sounds_config.json"
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
HOTKEYS = (
    ("ALT+M", "Activa o silencia el motor"),
    ("ALT+UP", "Sube el nivel de salida"),
    ("ALT+DOWN", "Reduce el nivel de salida"),
    ("CTRL+ESC", "Cierra la sesión residente"),
)
BUILD_SIGNATURE = "silent build / tray online / extended keymap"

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
        self.volume = DEFAULT_VOLUME
        self.enabled = True
        self.pressed_keys: set[tuple[int | None, str, str]] = set()
        self.sound_files = self._discover_sound_files()
        self.sound_cache: dict[Path, pygame.mixer.Sound] = {}
        self.cache_lock = threading.Lock()
        self.mixer_ready = False
        self._setup_mixer()
        self.load_settings()

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

    def _load_sound(self, path: Path) -> pygame.mixer.Sound:
        with self.cache_lock:
            sound = self.sound_cache.get(path)
            if sound is None:
                sound = pygame.mixer.Sound(str(path))
                self.sound_cache[path] = sound
            return sound

    def resolve_stem(self, event: keyboard.KeyboardEvent) -> str | None:
        name = normalize_name(event.name)

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

    def play_for_event(self, event: keyboard.KeyboardEvent) -> None:
        if not self.enabled or not self.mixer_ready:
            return

        stem = self.resolve_stem(event)
        if not stem:
            return

        sound_type = "press" if event.event_type == "down" else "release"
        sound_path = self.sound_files.get(stem, {}).get(sound_type)
        if sound_path is None and stem != UNKNOWN_STEM:
            sound_path = self.sound_files.get(UNKNOWN_STEM, {}).get(sound_type)
        if sound_path is None:
            return

        sound = self._load_sound(sound_path)
        sound.set_volume(self.volume)
        sound.play()

    def load_settings(self) -> None:
        if not CONFIG_FILE.exists():
            return

        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return

        self.volume = clamp(float(data.get("volume", self.volume)))
        self.enabled = bool(data.get("enabled", self.enabled))

    def save_settings(self) -> None:
        payload = {
            "volume": round(self.volume, 2),
            "enabled": self.enabled,
            "version": APP_VERSION,
        }
        CONFIG_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

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

    def handle_key_event(self, event: keyboard.KeyboardEvent) -> None:
        event_key = (getattr(event, "scan_code", None), normalize_name(event.name), event.event_type)
        opposite_key = (getattr(event, "scan_code", None), normalize_name(event.name), "down")

        if event.event_type == "down":
            if opposite_key in self.pressed_keys:
                return
            self.pressed_keys.add(event_key)
        else:
            self.pressed_keys.discard(opposite_key)

        self.play_for_event(event)

    def shutdown(self) -> None:
        keyboard.unhook_all()
        keyboard.clear_all_hotkeys()
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
        self.root.geometry("920x720")
        self.root.minsize(900, 700)

        icon_path = resolve_icon_path()
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except tk.TclError:
                pass

        self.status_var = tk.StringVar()
        self.substatus_var = tk.StringVar()
        self.volume_label_var = tk.StringVar()
        self.signature_var = tk.StringVar(value=BUILD_SIGNATURE.upper())
        self.volume_var = tk.IntVar(value=int(round(self.engine.volume * 100)))
        self.scanline_y = 0
        self.background_after_id: str | None = None

        self.tray_icon = pystray.Icon(
            APP_NAME,
            self.load_icon_image(),
            TRAY_TITLE,
            menu=pystray.Menu(
                pystray.MenuItem("Mostrar ventana", self._tray_show_window, default=True),
                pystray.MenuItem("Sonido activo", self._tray_toggle_enabled, checked=lambda item: self.engine.enabled),
                pystray.MenuItem("Salir", self._tray_exit),
            ),
        )

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.background = tk.Canvas(self.root, bd=0, highlightthickness=0, relief="flat", bg=BACKGROUND_LAYER_BOTTOM)
        self.background.grid(row=0, column=0, sticky="nsew")
        self.surface = tk.Frame(self.root, bg=BACKGROUND_LAYER_TOP)
        self.surface.place(relx=0.5, rely=0.5, relwidth=0.94, relheight=0.92, anchor="center")
        self.root.bind("<Configure>", self._on_root_configure)

        self._build_ui()
        self._register_keyboard_hooks()
        self.refresh_ui()
        self._draw_background()
        self._animate_background()

    def _build_ui(self) -> None:
        self.surface.grid_rowconfigure(0, weight=0)
        self.surface.grid_rowconfigure(1, weight=1)
        self.surface.grid_columnconfigure(0, weight=1)
        self.surface.grid_columnconfigure(1, weight=1)

        hero = self._create_panel(self.surface, row=0, column=0, columnspan=2, title="ACOUSTIC TYPE ENGINE", subtitle="Realtime resident keyboard ambience")
        controls = self._create_panel(self.surface, row=1, column=0, title="CONTROL CORE", subtitle="Manual override")
        output = self._create_panel(self.surface, row=1, column=1, title="OUTPUT MATRIX", subtitle="Click the bars to set intensity")

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
        tk.Label(
            left_hero,
            text="Future mechanical type ambience for Windows",
            bg=PANEL_ALT_COLOR,
            fg=TEXT_MUTED,
            font=("Consolas", 11),
            anchor="w",
        ).pack(anchor="w", pady=(4, 12))
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
            text=APP_VERSION,
            bg="#0f3542",
            fg=ACCENT_CYAN,
            font=("Consolas", 11, "bold"),
            padx=12,
            pady=6,
        )
        self.version_chip.pack(anchor="e", pady=(14, 12))
        self.health_stack = tk.Frame(right_hero, bg=PANEL_ALT_COLOR)
        self.health_stack.pack(anchor="e", fill="x")
        self.health_chips: list[tk.Label] = []
        for label in ("HOOK LIVE", "TRAY READY", "KEYMAP WIDE"):
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
            text="DEACTIVATE ENGINE",
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
            text="Window closes to tray, not to desktop. Silent mode stays armed until you exit.\nAlt+M toggle  |  Alt+Up raise  |  Alt+Down lower  |  Ctrl+Esc exit",
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
        self.hide_button = self._make_action_button(command_row, "MINIMIZE TO TRAY", self.hide_window, "#0a3340", ACCENT_CYAN)
        self.hide_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.exit_button = self._make_action_button(command_row, "EXIT SESSION", self.exit_application, "#31151a", ACCENT_RED)
        self.exit_button.pack(side="left", expand=True, fill="x", padx=(6, 0))

        output_body = output["body"]
        self.volume_display = tk.Label(
            output_body,
            textvariable=self.volume_label_var,
            bg=PANEL_COLOR,
            fg=TEXT_PRIMARY,
            font=("Bahnschrift SemiBold", 18, "bold"),
            anchor="w",
        )
        self.volume_display.pack(fill="x")
        self.volume_canvas = tk.Canvas(
            output_body,
            bg=PANEL_COLOR,
            bd=0,
            highlightthickness=0,
            height=178,
            relief="flat",
            cursor="hand2",
        )
        self.volume_canvas.pack(fill="both", expand=True, pady=(10, 10))
        self.volume_canvas.bind("<Button-1>", self._on_volume_canvas_click)

        output_controls = tk.Frame(output_body, bg=PANEL_COLOR)
        output_controls.pack(fill="x")
        self.decrease_button = self._make_action_button(output_controls, "- 5%", lambda: self._set_volume_and_refresh(self.engine.adjust_volume(-VOLUME_STEP)), "#102832", ACCENT_CYAN)
        self.decrease_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.increase_button = self._make_action_button(output_controls, "+ 5%", lambda: self._set_volume_and_refresh(self.engine.adjust_volume(VOLUME_STEP)), "#12362f", ACCENT_GREEN)
        self.increase_button.pack(side="left", expand=True, fill="x", padx=(6, 0))


    def _create_panel(
        self,
        parent: tk.Misc,
        *,
        row: int,
        column: int,
        title: str,
        subtitle: str,
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
        tk.Label(
            header,
            text=title,
            bg=PANEL_COLOR,
            fg=ACCENT_CYAN,
            font=("Bahnschrift SemiBold", 10, "bold"),
            anchor="w",
        ).pack(side="left")
        tk.Label(
            header,
            text=subtitle,
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            font=("Consolas", 9),
            anchor="e",
        ).pack(side="right")

        body = tk.Frame(panel, bg=PANEL_COLOR)
        body.pack(fill="both", expand=True)
        return {"panel": panel, "body": body}

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
        keyboard.add_hotkey("alt+m", self._hotkey_toggle_enabled)
        keyboard.add_hotkey("alt+up", self._hotkey_volume_up)
        keyboard.add_hotkey("alt+down", self._hotkey_volume_down)
        keyboard.add_hotkey("ctrl+esc", self._hotkey_exit)

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

        canvas.create_text(18, 16, text="AMPLITUDE BUS", anchor="w", fill=TEXT_MUTED, font=("Consolas", 10))
        canvas.create_text(
            width - 18,
            16,
            text="ACTIVE" if self.engine.enabled else "MUTED",
            anchor="e",
            fill=ACCENT_GREEN if self.engine.enabled else ACCENT_ORANGE,
            font=("Consolas", 10, "bold"),
        )

        normalized = (self.engine.volume - MIN_VOLUME) / (MAX_VOLUME - MIN_VOLUME)
        normalized = max(0.0, min(1.0, normalized))
        segments = 14
        active_segments = int(math.ceil(normalized * segments))
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

        canvas.create_text(left, height - 18, text="01%", anchor="w", fill=TEXT_MUTED, font=("Consolas", 9))
        canvas.create_text(width / 2, height - 18, text="VECTOR OUTPUT", anchor="center", fill=TEXT_MUTED, font=("Consolas", 9))
        canvas.create_text(right, height - 18, text="95%", anchor="e", fill=TEXT_MUTED, font=("Consolas", 9))

    def _on_volume_canvas_click(self, event: tk.Event) -> None:
        canvas = self.volume_canvas
        width = max(canvas.winfo_width(), 320)
        left = 22
        right = width - 22
        ratio = (event.x - left) / max(right - left, 1)
        ratio = max(0.0, min(1.0, ratio))
        self._set_volume_and_refresh(self.engine.set_volume(MIN_VOLUME + ratio * (MAX_VOLUME - MIN_VOLUME)))

    def refresh_ui(self) -> None:
        status = "ACTIVO" if self.engine.enabled else "SILENCIADO"
        mixer_state = "audio bus online" if self.engine.mixer_ready else "audio bus unavailable"
        self.status_var.set(f"Engine status: {status}\nMixer: {mixer_state}")
        self.substatus_var.set("resident keyboard hook / tray armed / zero-console launch")
        self.toggle_button.configure(
            text="DEACTIVATE ENGINE" if self.engine.enabled else "REACTIVATE ENGINE",
            bg="#114955" if self.engine.enabled else "#4f3017",
            activebackground="#15616e" if self.engine.enabled else "#ff9b54",
        )
        self.status_badge.configure(
            text="ACTIVE" if self.engine.enabled else "MUTED",
            bg=ACCENT_GREEN if self.engine.enabled else ACCENT_ORANGE,
            fg="#041015",
        )
        chip_specs = (
            ("HOOK LIVE" if self.engine.enabled else "HOOK IDLE", ACCENT_GREEN if self.engine.enabled else ACCENT_ORANGE),
            ("TRAY READY", ACCENT_CYAN),
            ("KEYMAP WIDE", ACCENT_CYAN),
        )
        for chip, (text, color) in zip(self.health_chips, chip_specs, strict=False):
            chip.configure(text=text, fg=color)
        self.volume_var.set(int(round(self.engine.volume * 100)))
        self.volume_label_var.set(f"OUTPUT LEVEL  {int(round(self.engine.volume * 100)):02d}%")
        self.tray_icon.title = f"{TRAY_TITLE} - {'Activo' if self.engine.enabled else 'Silenciado'}"
        self.tray_icon.update_menu()
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
