from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

raiz = Path(__file__).resolve().parent
salida = raiz.parent / "AA2_Pipeline_SistemaRestaurante_Proyecto.zip"
excluidos = {
    ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "build",
    "pdf-qa", "pdf-qa-final", "pdf-qa-apa7", "sistema_restaurante.egg-info", "temporal",
}

with ZipFile(salida, "w", ZIP_DEFLATED) as archivo:
    for ruta in sorted(raiz.rglob("*")):
        if not ruta.is_file():
            continue
        relativa = ruta.relative_to(raiz)
        if any(parte in excluidos for parte in relativa.parts):
            continue
        if ruta.name == ".coverage" or ruta.suffix in {".pyc", ".pyo"}:
            continue
        archivo.write(ruta, Path(raiz.name) / relativa)

with ZipFile(salida) as archivo:
    error = archivo.testzip()
    if error:
        raise RuntimeError(f"Archivo dañado dentro del ZIP: {error}")
    print(f"ZIP verificado: {salida}")
    print(f"Archivos incluidos: {len(archivo.namelist())}")
print(f"PDF incluido: {(raiz / 'AA2_Pipeline_SistemaRestaurante.pdf').stat().st_size} bytes")
