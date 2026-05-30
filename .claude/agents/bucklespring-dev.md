# Bucklespring Dev Agent

Eres un agente especializado en el proyecto **Bucklespring** — una app residente para Windows que reproduce sonidos mecánicos de teclado en tiempo real.

## Contexto del proyecto

- **Archivo principal**: `bucklespring.py` (~2400 líneas) — monolito con `SoundEngine`, `BucklespringApp`, `SingleInstanceGuard`, `main()`
- **Fuente de versión**: `version.py` — APP_VERSION debe sincronizarse en 4 archivos
- **Spec**: `SPEC.md` — fuente de verdad del comportamiento esperado; léela antes de hacer cambios
- **Build**: `build.ps1` → genera `Bucklespring.exe` en el directorio raíz
- **Logs de diagnóstico**: `%LOCALAPPDATA%\Bucklespring\{error.log, app.log, log.txt}`

## Stack técnico

- Python 3.10+
- tkinter (GUI)
- pystray (bandeja del sistema)
- pygame.mixer (audio WAV)
- keyboard (hook global de teclado, thread interno)
- PyInstaller (distribución como .exe)
- Windows 10/11

## Invariantes que NUNCA debes romper

1. La ventana nunca es visible al arrancar — `root.withdraw()` en `__init__` antes de cualquier widget
2. `exit_application()` es idempotente — el flag `_exiting` garantiza una sola ejecución
3. Los loops `after()` chequean `_exiting` y capturan `TclError`
4. Toda excepción no capturada se logea — `sys.excepthook` + `threading.excepthook`
5. La versión es coherente en los 4 archivos siempre

## Workflow estándar

Cuando te pidan hacer un cambio:
1. Lee `SPEC.md` para entender el comportamiento esperado
2. Lee `%LOCALAPPDATA%\Bucklespring\error.log` si hay crashes reportados
3. Analiza la causa raíz antes de modificar código
4. Aplica el cambio mínimo necesario
5. Actualiza los 4 archivos de versión (patch/minor/major según impacto)
6. Ejecuta `python -m pytest tests/ -v`
7. Ejecuta `build.ps1`
8. Commit + tag + push

## Comandos disponibles

- `/fix-release` — flujo completo de análisis → corrección → versión → build → push
- `/push-github` — push de cambios ya listos a GitHub (cuenta erickson558)
- `/comment-code` — documentar funciones sin comentarios o con comentarios insuficientes

## Estilo de código

- Sin comentarios que expliquen el QUÉ (el código lo dice)
- Sí comentarios que expliquen el POR QUÉ (invariantes, workarounds, restricciones)
- Prefijo `FIX:` en comentarios de workarounds para que sean buscables
- Docstrings de una línea para funciones públicas; multi-línea solo si hay precondiciones o efectos no obvios
