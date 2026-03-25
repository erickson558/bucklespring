# Bucklespring

Bucklespring reproduce sonidos mecánicos de teclado en Windows usando un hook global de teclado, una GUI futurista con `tkinter` y un icono residente en la bandeja del sistema.

## Versión actual

`V1.4.1`

El proyecto usa versionado `Vx.x.x` con criterio semántico:
- `major`: cambios incompatibles.
- `minor`: nuevas funciones compatibles.
- `patch`: correcciones o ajustes sin romper compatibilidad.

## Funcionalidades

- GUI futurista estilo HUD para activar o desactivar el sonido sin abrir consola.
- Barra de menús estilo Windows con `Archivo`, `Configuracion` y `Ayuda`.
- Icono en la bandeja del sistema, junto al reloj de Windows.
- Dial de volumen interactivo dentro de la GUI.
- Persistencia de volumen, estado y hotkeys en `config.json`.
- About dialog con versión y autor.
- Laboratorio `Fn Capture Lab` para inspeccionar eventos crudos de teclado.
- Ruta de audio no bloqueante para evitar congelamientos de la GUI.
- Atajos globales:
  - Editables desde la GUI y persistentes entre reinicios.
  - Incluyen activar/silenciar, subir, bajar, enviar al tray y salir.
- Resolución mejorada de teclas:
  - Soporta teclas estándar por `scan code`.
  - Añade cobertura para `Win`, `Shift`, `AltGr`, flechas y teclas extendidas.
  - Usa un sonido genérico de fallback para cualquier tecla que sí emita evento pero no tenga mapeo dedicado.

## Cambios recientes

- `V1.4.1`: corrección del workflow de release para que el tag y el GitHub Release se generen correctamente a partir de `main`.
- `V1.4.0`: barra de menús con About, laboratorio de captura `Fn`, pipeline de audio no bloqueante y versión visible en más puntos de la GUI.
- `V1.3.0`: dial interactivo, hotkeys configurables con `config.json`, salida segura al tray y rango de volumen 0-100%.
- `V1.2.0`: rediseño futurista de la GUI, panel de volumen visual tipo matriz y mejoras estéticas del panel residente.
- `V1.1.0`: GUI base, bandeja del sistema, build silencioso y cobertura ampliada de teclas.

## Dependencias

- Python 3.12
- `keyboard`
- `pygame`
- `pystray`
- `Pillow`
- `pyinstaller`

## Uso

1. Instala dependencias:

```powershell
python -m pip install -r requirements.txt
```

2. Ejecuta en modo desarrollo:

```powershell
python .\bucklespring.py
```

3. Consulta la versión actual:

```powershell
python .\bucklespring.py --version
```

## Compilación

El build genera un único ejecutable `Bucklespring.exe` en la misma carpeta del `.py`, usa `bucklespring.ico` y no levanta consola.

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Bucklespring --icon bucklespring.ico --version-file .\file_version_info.txt --distpath . --workpath build --specpath . --add-data "audios;audios" --add-data "bucklespring.ico;." --hidden-import pystray._win32 --exclude-module pygame.tests --exclude-module pygame.examples .\bucklespring.py
```

También puedes usar el script reproducible:

```powershell
.\build.ps1
```

## Release automático

Cada push a `main` ejecuta `.github/workflows/release.yml` para:

- leer `APP_VERSION` desde `version.py`
- compilar `Bucklespring.exe`
- validar o crear el tag de la versión actual
- generar o actualizar el release de GitHub
- adjuntar el `.exe` y usar la sección correspondiente de `CHANGELOG.md` como notas

## Archivos relevantes

- `bucklespring.py`: aplicación principal.
- `version.py`: nombre y versión.
- `audios/`: sonidos `.wav`.
- `bucklespring.ico`: icono para bandeja y build.
- `file_version_info.txt`: metadatos de versión incrustados en el `.exe`.
- `build.ps1`: script de build reproducible para generar el `.exe`.
- `.github/workflows/release.yml`: build y release automático en GitHub Actions.

## Notas

- La tecla `Fn` normalmente no genera eventos estándar en Windows porque depende del firmware del teclado. La app intenta usar un fallback genérico si el sistema sí reporta ese evento, pero no hay garantía absoluta de captura en todos los teclados.
- Si existe una carpeta `audios` junto al `.exe`, la app la usa primero. Si no existe, usa los audios empaquetados en el binario.

## Licencia

Apache License 2.0. Ver [`LICENSE`](LICENSE).
