"""Utilidad de terminal para gestionar los PDFs de la memoria (sin abrir el chat).

Uso (desde la raíz del proyecto):
    python src/memoria_rag/ingesta_pdf.py subir  documentos/manual.pdf
    python src/memoria_rag/ingesta_pdf.py buscar "¿cómo se configura el sistema?"
    python src/memoria_rag/ingesta_pdf.py listar
    python src/memoria_rag/ingesta_pdf.py borrar manual.pdf

En el chat (main.py) también puede usar el comando /pdf <ruta>.
"""
import sys

from almacen import crear_cliente, obtener_coleccion
from memoria_documentos import MemoriaDocumentos

NOMBRE_COLECCION = "documentos_pdf"


def abrir() -> MemoriaDocumentos:
    return MemoriaDocumentos(obtener_coleccion(crear_cliente(), NOMBRE_COLECCION))


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else ""
    argumento = " ".join(sys.argv[2:])
    if comando not in {"subir", "buscar", "listar", "borrar"} or (
        comando != "listar" and not argumento
    ):
        print(__doc__)
        sys.exit(1)

    docs = abrir()
    if comando == "subir":
        print(f"Listo: {docs.subir_pdf(argumento)} fragmentos guardados.")
    elif comando == "buscar":
        for r in docs.recuperar(argumento):
            print(f"[{r['fuente']}, pág. {r['pagina']}, dist. {r['distancia']:.2f}]\n{r['texto']}\n")
    elif comando == "listar":
        for nombre, n in docs.listar().items():
            print(f"- {nombre}: {n} fragmentos")
    else:
        docs.eliminar(argumento)
        print(f"Borrado: {argumento}")
