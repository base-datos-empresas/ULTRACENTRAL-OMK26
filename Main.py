#!/usr/bin/env python3
import os
import glob
from colorama import Fore, Style, init
from configuracion import INPUT_FOLDER, OUTPUT_FOLDER, EXCLUSIONES_FOLDER
from exclusions import cargar_exclusiones
from processors.process_csv import process_csv

init(autoreset=True)

DEMO_MODE = False

def display_menu():
    """
    Muestra un menú para seleccionar el modo de procesamiento:
      1. Procesar todos los registros (modo completo)
      2. Procesar solo los primeros 20 registros (modo demo)
    """
    global DEMO_MODE
    while True:
        print(Style.BRIGHT + Fore.CYAN + "\n============================================================")
        print("📌 SELECCIONE EL MODO DE PROCESAMIENTO:")
        print("1️⃣  Procesar todos los registros (modo completo)")
        print("2️⃣  Procesar solo los primeros 20 registros (modo demo)")
        print("============================================================")
        choice = input(Fore.YELLOW + "Ingrese su elección (1 o 2): ").strip()

        if choice == "1":
            DEMO_MODE = False
            print(Fore.GREEN + "✅ Procesamiento completo seleccionado.")
            break
        elif choice == "2":
            DEMO_MODE = True
            print(Fore.BLUE + "🔹 Modo demo seleccionado. Solo se procesarán 20 registros.")
            break
        else:
            print(Fore.RED + "❌ Opción inválida. Por favor, ingrese '1' o '2'.")

def ensure_folders_exist():
    """
    Verifica y crea, si no existen, las carpetas requeridas:
      - 1Inputs
      - Publicar
      - xclusiones
    """
    for folder in [INPUT_FOLDER, OUTPUT_FOLDER, EXCLUSIONES_FOLDER]:
        if not os.path.exists(folder):
            print(Fore.YELLOW + f"📂 Creando carpeta: {folder}")
            os.makedirs(folder, exist_ok=True)

def main():
    """
    Orquesta el proceso general:
      1. Asegura la existencia de las carpetas de trabajo.
      2. Carga las palabras de exclusión.
      3. Muestra el menú interactivo (modo completo o demo).
      4. Busca y procesa los archivos CSV en la carpeta '1Inputs'.
      5. Llama a la función 'process_csv' para cada archivo, pasando la lista de exclusiones y el modo seleccionado.
    """
    print(Style.BRIGHT + Fore.CYAN + "============================================================")
    print("🚀 INICIO DEL PROCESAMIENTO DE CSVs 🚀")
    print("============================================================")

    ensure_folders_exist()
    exclusiones = cargar_exclusiones()
    display_menu()

    csv_files = glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))
    if not csv_files:
        print(Fore.RED + f"🚨 No se encontraron archivos CSV en '{INPUT_FOLDER}'.")
        return

    for csv_file in csv_files:
        process_csv(csv_file, exclusiones, DEMO_MODE)

    print(Fore.GREEN + "🎉 Procesamiento completado. Revisa los archivos en la carpeta de salida.")

if __name__ == "__main__":
    main()
