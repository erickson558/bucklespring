# Bucklespring

Bucklespring reproduce sonidos mecánicos de teclado en Windows usando un hook global de teclado, una GUI futurista con `tkinter` y un icono residente en la bandeja del sistema.

## Versión actual

`V1.5.5`

El proyecto usa versionado `Vx.x.x` con criterio semántico:
- `major`: cambios incompatibles.
- `minor`: nuevas funciones compatibles.
- `patch`: correcciones o ajustes sin romper compatibilidad.

## Funcionalidades

- GUI futurista estilo HUD para activar o desactivar el sonido sin abrir consola.
- Barra de menús estilo Windows con `Archivo`, `Configuracion` y `Ayuda`.
- Selector de idioma en la barra de menús con cambio en caliente entre ingles y espanol.
- Icono en la bandeja del sistema, junto al reloj de Windows.
- Dial de volumen interactivo dentro de la GUI.
- Persistencia de volumen, estado, idioma y hotkeys en `config.json`.
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

- `V1.5.5`: la app ahora inicia minimizada al tray sin mostrar la ventana; loop de animación de fondo suspendido cuando la ventana está oculta (ahorro de CPU); fix de eventos `<Unmap>` espurios propagados desde widgets hijos.
- `V1.5.3`: log de sesión (`app.log`) con registro de arranque, cierre y duplicados; instancia única mejorada con bring-to-front automático y aviso informativo cuando la app ya está activa en el tray; fix de doble `save_settings()` al ajustar volumen desde botones.
- `V1.5.2`: corrección de crash silencioso al arrancar — mutex `Global\` con fallback a `Local\`, `keyboard.hook()` protegido con `try/except`, `BucklespringApp()` envuelto en manejo de errores con messagebox diagnóstico, log de errores a `%LOCALAPPDATA%\Bucklespring\error.log`, cancelación correcta del loop de diagnóstico al salir, y comentarios exhaustivos en todo el código.
- `V1.5.1`: el worker de audio ahora sobrevive a WAV dañados o ausentes, se ignoran liberaciones huérfanas para evitar clics fantasma y la configuración cae a una ruta segura si la carpeta de la app no permite escritura.
- `V1.5.0`: soporte multi-idioma para la GUI con cambio desde la barra de menús y persistencia del idioma seleccionado.
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
- Si la carpeta del programa no permite escribir `config.json`, la app guarda la configuración en `%LOCALAPPDATA%\\Bucklespring\\config.json` sin interrumpir el audio ni la GUI.

## Licencia

Apache License 2.0. Ver [`LICENSE`](LICENSE).
