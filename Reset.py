#!/usr/bin/env python3
import os
import shutil

# Definición de las carpetas a limpiar
INPUT_FOLDER = "1Inputs"
OUTPUT_FOLDER = "Publicar"


def clear_folder(folder):
    """
    Elimina todo el contenido dentro de la carpeta especificada sin borrar la carpeta.
    """
    if os.path.exists(folder):
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Error al borrar {item_path}: {e}")
        print(f"Contenido de la carpeta '{folder}' borrado correctamente.")
    else:
        print(f"La carpeta '{folder}' no existe.")


def main():
    print("=== Script de Resets ===")
    print("Seleccione la opción:")
    print("1. Borrar el contenido solo de la carpeta 'Publicar' (por defecto)")
    print("2. Borrar el contenido de ambas carpetas: 'Publicar' y '1Inputs'")

    opcion = input("Ingrese su elección (1 o 2, Enter para opción por defecto): ").strip()

    if opcion == "2":
        print("\nSe borrará el contenido de ambas carpetas: 'Publicar' y '1Inputs'.")
        clear_folder(OUTPUT_FOLDER)
        clear_folder(INPUT_FOLDER)
    else:
        print("\nSe borrará el contenido solo de la carpeta 'Publicar'.")
        clear_folder(OUTPUT_FOLDER)


if __name__ == "__main__":
    main()
