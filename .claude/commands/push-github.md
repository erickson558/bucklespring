# push-github — Subir cambios a GitHub

Sube los cambios actuales al repositorio de GitHub usando la cuenta **erickson558**.

## Verificaciones previas

1. Confirma que la versión es consistente en los 4 archivos:
   - `version.py` → `APP_VERSION`
   - `file_version_info.txt` → `FileVersion` y `ProductVersion`
   - `README.md` → "Versión actual"
   - `CHANGELOG.md` → entrada más reciente

2. Verifica el estado de git:

```powershell
git status
git log --oneline -5
```

## Secuencia de push

Detecta la versión actual desde `version.py` y ejecuta:

```powershell
# Staging de los archivos del release
git add bucklespring.py version.py file_version_info.txt README.md CHANGELOG.md Bucklespring.exe

# Si hay SPEC.md u otros archivos relevantes, agregarlos también
git add SPEC.md

# Commit con formato conventional commit
git commit -m "fix/feat: <descripción> (Vx.x.x)"

# Tag de versión
git tag Vx.x.x

# Push a main y al tag
git push origin main
git push origin Vx.x.x
```

## Notas

- Cuenta activa: **erickson558** (autenticado vía keyring)
- Protocolo: HTTPS
- Branch principal: `main`
- NO usar `--force` a menos que se indique explícitamente
- NO saltar hooks de pre-commit (`--no-verify`)

## Verificación post-push

```powershell
git log --oneline -3
git tag --list | Select-Object -Last 5
```

Confirma que el tag y el commit aparecen en remoto.
