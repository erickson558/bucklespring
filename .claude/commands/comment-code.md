# comment-code — Comentar y documentar el código

Analiza el código de Bucklespring y agrega o mejora comentarios explicativos para que cualquier desarrollador entienda qué hace cada parte.

## Alcance

Por defecto trabaja sobre `bucklespring.py`. Si el usuario especifica un archivo o función, enfócate en esa parte.

## Reglas de comentado

### QUÉ comentar
- El **POR QUÉ** de decisiones no obvias (invariantes, workarounds, restricciones de plataforma)
- Precondiciones y postcondiciones de funciones públicas
- Efectos secundarios (I/O, estado compartido, threads)
- Trampas conocidas (thread safety, orden de llamadas, race conditions)

### QUÉ NO comentar
- Lo que ya dice el nombre de la función o variable
- Código autoexplicativo
- Comentarios del tipo "incrementa x en 1" para `x += 1`

## Formato de docstrings (Python)

```python
def funcion(arg: tipo) -> tipo:
    """
    Una línea describiendo QUÉ hace.

    Precondiciones: ...
    Efectos secundarios: ...
    Thread safety: ...
    """
```

## Proceso

1. Lee el archivo/sección indicada
2. Identifica funciones y bloques sin comentarios o con comentarios insuficientes
3. Agrega comentarios siguiendo las reglas anteriores
4. NO modifica lógica — solo agrega/mejora comentarios
5. Reporta qué secciones se comentaron y por qué eran importantes documentar

## Ejemplo de salida

```
Secciones comentadas:
- SoundEngine._load_sound(): explicación de por qué se usa failed_sound_paths
- BucklespringApp._on_unmap(): por qué el guard event.widget is self.root es crítico
- main()._global_excepthook: por qué es necesario para el .exe sin consola
```
