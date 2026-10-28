"""Memoria de documentos: lee PDFs, los fragmenta y los recupera con RAG."""
import hashlib
from pathlib import Path

from pypdf import PdfReader

TAM_FRAGMENTO = 1000   # caracteres por fragmento
SOLAPE = 200           # caracteres compartidos entre fragmentos contiguos
TAM_LOTE = 64          # fragmentos por inserción en Chroma


# ---------------------------------------------------------------- Lector
def extraer_paginas(ruta_pdf: str) -> list[tuple[int, str]]:
    """Devuelve [(numero_pagina, texto), ...] ignorando las páginas vacías."""
    lector = PdfReader(ruta_pdf)
    paginas = []
    for i, pagina in enumerate(lector.pages, start=1):
        texto = (pagina.extract_text() or "").strip()
        if texto:
            paginas.append((i, texto))
    return paginas


def dividir_texto(texto: str, tam: int = TAM_FRAGMENTO, solape: int = SOLAPE) -> list[str]:
    """Parte el texto en fragmentos con solape, intentando cortar en espacios."""
    fragmentos = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + tam, len(texto))
        if fin < len(texto):
            corte = texto.rfind(" ", inicio + tam // 2, fin)
            if corte != -1:
                fin = corte
        fragmento = texto[inicio:fin].strip()
        if fragmento:
            fragmentos.append(fragmento)
        if fin >= len(texto):
            break
        inicio = max(fin - solape, inicio + 1)
    return fragmentos


# ------------------------------------------------------------- Memoria
class MemoriaDocumentos:
    def __init__(self, coleccion):
        self.coleccion = coleccion

    def subir_pdf(self, ruta_pdf: str) -> int:
        """Lee un PDF y lo guarda en la base vectorial. Devuelve nº de fragmentos."""
        ruta = Path(ruta_pdf).expanduser()
        if not ruta.is_file():
            raise FileNotFoundError(f"No existe el archivo: {ruta}")
        if ruta.suffix.lower() != ".pdf":
            raise ValueError(f"El archivo no es un PDF: {ruta.name}")

        ids, textos, metadatos = [], [], []
        for num_pagina, texto in extraer_paginas(str(ruta)):
            for n, fragmento in enumerate(dividir_texto(texto)):
                # ID determinista: subir dos veces el mismo PDF no duplica datos
                huella = hashlib.md5(fragmento.encode("utf-8")).hexdigest()[:10]
                ids.append(f"{ruta.stem}-p{num_pagina}-{n}-{huella}")
                textos.append(fragmento)
                metadatos.append({"fuente": ruta.name, "pagina": num_pagina, "fragmento": n})

        if not textos:
            raise ValueError("El PDF no contiene texto extraíble (¿es un escaneo? Necesita OCR).")

        # Si el PDF cambió de contenido, se borra la versión anterior primero
        self.eliminar(ruta.name)
        for i in range(0, len(textos), TAM_LOTE):
            self.coleccion.upsert(
                ids=ids[i:i + TAM_LOTE],
                documents=textos[i:i + TAM_LOTE],
                metadatas=metadatos[i:i + TAM_LOTE],
            )
        return len(textos)

    def recuperar(self, consulta: str, k: int = 4, distancia_max: float = 0.75,
                  fuente: str | None = None) -> list[dict]:
        """Fragmentos más parecidos a la consulta (distancia coseno: 0 = idéntico)."""
        total = self.coleccion.count()
        if total == 0:
            return []
        r = self.coleccion.query(
            query_texts=[consulta],
            n_results=min(k, total),
            where={"fuente": fuente} if fuente else None,
            include=["documents", "metadatas", "distances"],
        )
        return [
            {"texto": doc, "fuente": meta["fuente"], "pagina": meta["pagina"], "distancia": dist}
            for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])
            if dist <= distancia_max
        ]

    def listar(self) -> dict[str, int]:
        """Devuelve {nombre_pdf: nº de fragmentos} de lo que hay guardado."""
        metas = self.coleccion.get(include=["metadatas"])["metadatas"]
        conteo: dict[str, int] = {}
        for m in metas:
            conteo[m["fuente"]] = conteo.get(m["fuente"], 0) + 1
        return conteo

    def eliminar(self, fuente: str) -> None:
        """Borra todos los fragmentos de un PDF (por nombre de archivo)."""
        self.coleccion.delete(where={"fuente": fuente})
