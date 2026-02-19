# Guía para actualizar dependencias con uv

## Flujo completo

### 1. Actualizar la versión en `pyproject.toml`

Editá la versión mínima de la dependencia que querés actualizar:

```toml
# Antes
"fastapi>=0.121.1",

# Después
"fastapi>=0.122.0",
```

### 2. Regenerar el lockfile

```bash
uv lock
```

Esto resuelve las dependencias y actualiza `uv.lock` respetando las restricciones de `pyproject.toml`.

> **Tip**: Si querés actualizar **todas** las dependencias a la última versión compatible:
> ```bash
> uv lock --upgrade
> ```
> Para actualizar solo una dependencia específica:
> ```bash
> uv lock --upgrade-package fastapi
> ```

### 3. Exportar a `requirements.txt`

```bash
uv export --output-file requirements.txt --no-hashes
```

### 4. Instalar en el entorno virtual

```bash
uv pip install -r requirements.txt
```

O para sincronizar (instala nuevas, elimina las que ya no están):

```bash
uv pip sync requirements.txt
```

### 5. Verificar que todo funcione

```bash
# Correr tests
pytest

# Levantar la app
uvicorn app.main:app --reload
```

### 6. Commitear los cambios

```bash
git add pyproject.toml uv.lock requirements.txt
git commit -m "chore(deps): bump fastapi to 0.122.0"
```

## Resumen rápido

```
pyproject.toml  →  uv lock  →  uv export  →  uv pip install  →  test  →  commit
```

| Archivo | Qué hace | ¿Va en git? |
|---|---|---|
| `pyproject.toml` | Define versiones mínimas | Sí |
| `uv.lock` | Versiones exactas resueltas | Sí |
| `requirements.txt` | Exportado para deploy/CI | Sí |
