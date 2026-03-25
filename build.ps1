$ErrorActionPreference = "Stop"
$env:PYGAME_HIDE_SUPPORT_PROMPT = "1"

python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name Bucklespring `
  --icon .\bucklespring.ico `
  --version-file .\file_version_info.txt `
  --distpath . `
  --workpath .\build `
  --specpath . `
  --add-data "audios;audios" `
  --add-data "bucklespring.ico;." `
  --hidden-import pystray._win32 `
  --exclude-module pygame.tests `
  --exclude-module pygame.examples `
  .\bucklespring.py
