# Bucklespring — Especificación del Proyecto (SDD)

> **Spec Driven Development**: este documento es la fuente de verdad del proyecto.
> Cualquier cambio de comportamiento se especifica aquí ANTES de tocar el código.

---

## 1. Propósito y alcance

Bucklespring es una aplicación residente para Windows que reproduce sonidos mecánicos de teclado en tiempo real mediante un hook global de teclado. Se ejecuta en la bandeja del sistema sin ventana visible, con una GUI de diagnóstico accesible bajo demanda.

**Fuera de alcance:** soporte macOS/Linux, síntesis de audio, grabación de pulsaciones, integración con otros procesos.

---

## 2. Arquitectura del sistema

```
main()
 ├── SingleInstanceGuard     — Mutex Win32 (Global\ con fallback a Local\)
 ├── BucklespringApp.__init__
 │    ├── SoundEngine         — Audio + hook de teclado + config
 │    │    ├── pygame.mixer   — Reproducción WAV (44.1 kHz, 16-bit, estéreo)
 │    │    ├── keyboard.hook  — Hook global de teclado (thread interno)
 │    │    └── audio_worker   — Thread daemon: consume queue → reproduce
 │    ├── tk.Tk (withdrawn)   — Ventana oculta desde __init__
 │    ├── pystray.Icon        — Icono de bandeja (thread separado)
 │    └── after() loops       — _animate_background (90ms/500ms) + _drain_diagnostic (80ms)
 └── BucklespringApp.start()
      ├── tray_icon.run_detached()
      ├── root.withdraw()     — Defensivo (ya retirada en __init__)
      └── root.mainloop()     — Bloquea hasta exit_application()
```

---

## 3. Especificaciones de comportamiento

### 3.1 Inicio de la aplicación

| Condición | Comportamiento esperado |
|-----------|------------------------|
| Primera instancia | Arranca silencioso en el tray, ventana nunca visible |
| Segunda instancia | `FindWindowW` trae la ventana al frente; si no hay HWND visible, muestra messagebox informativo |
| Fallo de mutex Win32 | Continúa sin guard (best-effort), logea a `error.log` |
| Fallo de `pygame.mixer` | App arranca sin audio; `mixer_ready = False` |
| Fallo de `keyboard.hook` | App arranca sin sonido; error logado |

### 3.2 Audio

| Condición | Comportamiento esperado |
|-----------|------------------------|
| Tecla presionada | Reproduce WAV `<scan>-0.wav`; fallback a `ff-0.wav` |
| Tecla liberada | Reproduce WAV `<scan>-1.wav`; fallback a `ff-1.wav` |
| WAV corrupto/faltante | Marca path en `failed_sound_paths`; nunca reintenta ese archivo |
| Tecla repetida (key held) | Ignorada (sin audio extra) |
| Release huérfano | Ignorado (no hubo down previo) |
| Motor deshabilitado | Hook activo pero sin reproducción |

### 3.3 Tray y ventana

| Condición | Comportamiento esperado |
|-----------|------------------------|
| Clic en ×  de la ventana | `hide_window()` — ventana retirada, tray activo |
| Minimizar nativo (botón -) | `_on_unmap` detecta `"iconic"` → `hide_window()` |
| Doble clic en tray | `show_window()` — ventana visible y en frente |
| Hotkey SEND TO TRAY | `hide_window()` |
| Hotkey EXIT SESSION | `exit_application()` |
| Cierre simultáneo (hotkey + tray) | Solo el primer `exit_application()` actúa (guard `_exiting`) |

### 3.4 Configuración persistente

- Ruta primaria: mismo directorio que el `.exe`
- Ruta de respaldo: `%LOCALAPPDATA%\Bucklespring\config.json`
- Campos: `volume`, `enabled`, `language`, `hotkeys`, `version`
- Validación: volumen clampeado a [0.0, 1.0]; hotkeys validados con `keyboard.parse_hotkey()`

### 3.5 Idiomas soportados

| Código | Idioma |
|--------|--------|
| `en`   | Inglés (predeterminado) |
| `es`   | Español |

El idioma se cambia en caliente desde el menú `Language` sin reiniciar la app.

### 3.6 Logs del sistema

| Archivo | Ruta | Contenido |
|---------|------|-----------|
| `app.log` | `%LOCALAPPDATA%\Bucklespring\app.log` | SESSION START/END, duplicados, crashes |
| `error.log` | `%LOCALAPPDATA%\Bucklespring\error.log` | Excepciones no capturadas, fallos de init |
| `log.txt` | `%LOCALAPPDATA%\Bucklespring\log.txt` | Eventos detallados con thread name |

---

## 4. Invariantes del sistema (no romper nunca)

1. **La ventana NUNCA es visible en el arranque** — `root.withdraw()` ocurre en `__init__` antes de construir ningún widget visible.
2. **`exit_application()` es idempotente** — el flag `_exiting` garantiza que solo la primera llamada actúa.
3. **Los loops `after()` nunca crashean al cerrar** — todos chequean `_exiting` antes de reprogramarse y capturan `TclError`.
4. **El worker de audio es daemon thread** — muere automáticamente si el proceso termina por cualquier razón.
5. **Toda excepción no capturada se logea** — `sys.excepthook` + `threading.excepthook` cubren main thread y threads secundarios.
6. **La versión es coherente en 4 archivos** — `version.py`, `file_version_info.txt`, `README.md`, `CHANGELOG.md`.

---

## 5. Contratos de calidad

| Atributo | Requisito |
|----------|-----------|
| Latencia de audio | < 50 ms desde pulsación hasta reproducción |
| CPU en tray (oculto) | < 1% (animación a 500 ms, audio solo on-demand) |
| Memoria | < 80 MB en uso normal |
| Crash rate | Cero crashes silenciosos — todo queda en `error.log` |
| Compatibilidad | Windows 10/11, Python 3.10+ o .exe standalone |

---

## 6. Flujo de versioning

```
Cambio de código
    ↓
Análisis de impacto (patch / minor / major)
    ↓
Actualizar los 4 archivos de versión
    ↓
Build del .exe con build.ps1
    ↓
Commit: "fix/feat: descripción (Vx.x.x)"
    ↓
Tag: git tag Vx.x.x
    ↓
Push: git push origin main && git push origin Vx.x.x
```

### Criterio de incremento

| Tipo | Cuándo |
|------|--------|
| `patch` x.x.+1 | Bug fixes, mejoras de estabilidad, docs |
| `minor` x.+1.0 | Nueva funcionalidad compatible |
| `major` +1.0.0 | Cambios incompatibles de API o comportamiento |

---

## 7. Estructura de archivos

```
bucklingspring/
├── bucklespring.py          # Monolito principal (~2400 líneas)
├── version.py               # APP_VERSION, APP_NAME, APP_AUTHOR, APP_LICENSE
├── file_version_info.txt    # PE metadata para PyInstaller (debe coincidir con version.py)
├── build.ps1                # Script de compilación PyInstaller → Bucklespring.exe
├── requirements.txt         # Dependencias Python
├── config.json              # Config en runtime (generado, no versionado como artefacto)
├── bucklespring.ico          # Icono de ventana y tray
├── audios/                  # WAVs: <hex>-0.wav (press), <hex>-1.wav (release)
├── SPEC.md                  # Este archivo — fuente de verdad del comportamiento
├── README.md                # Documentación de usuario
├── CHANGELOG.md             # Historial de cambios por versión
└── tests/
    └── test_bucklespring.py # Tests unitarios del motor de audio
```

---

## 8. Reglas de desarrollo (SDD)

1. **Spec primero**: toda nueva funcionalidad o cambio de comportamiento se documenta aquí antes de implementarse.
2. **No romper invariantes**: cualquier cambio que viole la sección 4 requiere revisión explícita.
3. **Análisis antes de código**: identificar causa raíz antes de tocar cualquier línea.
4. **Comentarios explicativos**: cada función pública documenta su propósito, precondiciones y efectos secundarios.
5. **Un commit por versión**: los 6 archivos (py, version, file_version_info, README, CHANGELOG, exe) van en el mismo commit.
