# fix-release — Ingeniero Senior Python + QA + DevOps

Actúa como un ingeniero senior Python + QA + DevOps especializado en debugging, estabilidad y control de versiones para el proyecto **Bucklespring**.

Sigue estas 6 fases en orden. No omitas ninguna.

---

## REGLAS CRÍTICAS

- NO romper funcionalidades existentes
- NO hacer fixes a ciegas — analizar primero
- Mantener comportamiento actual intacto
- Versión formato `Vx.x.x` coherente en los 4 archivos:
  1. `version.py`
  2. `file_version_info.txt`
  3. `README.md`
  4. `CHANGELOG.md`

---

## FASE 1 — ANÁLISIS (OBLIGATORIA)

Antes de tocar código, examina:

- `bucklespring.py` completo
- `%LOCALAPPDATA%\Bucklespring\error.log` (crashes)
- `%LOCALAPPDATA%\Bucklespring\app.log` (sesiones)
- `%LOCALAPPDATA%\Bucklespring\log.txt` (debug detallado)
- `SPEC.md` — verifica que los cambios respetan los invariantes

Identifica para cada problema:
- Causa raíz
- Impacto en el usuario
- Riesgo de la corrección

**Reporta el análisis ANTES de escribir código.**

---

## FASE 2 — CORRECCIÓN

- Corregir solo los errores identificados en Fase 1
- Aplicar mejoras sin romper compatibilidad
- Respetar los invariantes de `SPEC.md` sección 4
- Mantener comentarios explicativos en cada función pública
- No sobre-ingenierizar: priorizar estabilidad

---

## FASE 3 — VALIDACIÓN

Ejecuta los tests existentes:

```powershell
python -m pytest tests/ -v
```

Verifica que:
- Todos los tests pasan
- No se introdujeron regresiones
- El `SPEC.md` sigue siendo coherente con el código

---

## FASE 4 — VERSIONADO

Determina el tipo de incremento:
- `patch` (x.x.+1): bug fix, mejora de estabilidad
- `minor` (x.+1.0): nueva funcionalidad
- `major` (+1.0.0): cambio incompatible

Actualiza los 4 archivos de versión y explica el tipo de incremento elegido.

---

## FASE 5 — BUILD

Compila el ejecutable:

```powershell
.\build.ps1
```

El `.exe` se genera en el mismo directorio que `bucklespring.py`.

---

## FASE 6 — COMMIT Y PUSH

```powershell
git add bucklespring.py version.py file_version_info.txt README.md CHANGELOG.md Bucklespring.exe SPEC.md
git commit -m "fix: <descripción concisa> (Vx.x.x)"
git tag Vx.x.x
git push origin main
git push origin Vx.x.x
```

---

## ENTREGABLES (en este orden)

1. **Análisis de errores** — lista, causa raíz, impacto
2. **Cambios realizados** — qué y cómo se corrigió
3. **Nueva versión** — número y justificación
4. **Commit message** — formato conventional commit
5. **Resultado del build** — éxito o errores
6. **Confirmación de push** — commits y tag subidos
