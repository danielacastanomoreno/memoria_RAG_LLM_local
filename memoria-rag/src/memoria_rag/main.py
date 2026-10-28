"""Chat de consola con memoria a corto, medio y largo plazo y lector de PDF."""
from gestor import GestorMemoria

AYUDA = (
    "Comandos:\n"
    "  /pdf <ruta>      carga un PDF para poder preguntarle cosas\n"
    "  /docs            lista los PDFs cargados\n"
    "  /borrar <nombre> elimina un PDF (por nombre de archivo)\n"
    "  salir            guarda la sesión y termina\n"
)


def comando(gestor: GestorMemoria, texto: str) -> None:
    """Ejecuta un comando que empieza por '/'."""
    nombre, _, argumento = texto.partition(" ")
    argumento = argumento.strip().strip("'\"")  # admite rutas arrastradas a la terminal
    try:
        if nombre == "/pdf" and argumento:
            n = gestor.cargar_pdf(argumento)
            print(f"Sistema: PDF cargado ({n} fragmentos). Ya puede preguntarme sobre él.\n")
        elif nombre == "/docs":
            docs = gestor.docs.listar()
            if not docs:
                print("Sistema: no hay PDFs cargados.\n")
            for archivo, n in docs.items():
                print(f"  - {archivo} ({n} fragmentos)")
            print()
        elif nombre == "/borrar" and argumento:
            gestor.docs.eliminar(argumento)
            print(f"Sistema: {argumento} eliminado.\n")
        else:
            print(AYUDA)
    except (FileNotFoundError, ValueError) as error:
        print(f"Sistema: {error}\n")


def main():
    gestor = GestorMemoria()
    print("Chat con memoria. Escriba /ayuda para ver los comandos.\n")
    while True:
        texto = input("Usted: ").strip()
        if texto.lower() in {"salir", "exit"}:
            gestor.cerrar_sesion()
            print("Sesión guardada. Hasta pronto.")
            break
        if texto.startswith("/"):
            comando(gestor, texto)
        elif texto:
            print(f"Asistente: {gestor.conversar(texto)}\n")


if __name__ == "__main__":
    main()
