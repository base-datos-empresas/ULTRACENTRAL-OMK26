import os
import glob
import pandas as pd
from colorama import Fore, Style, init
from crawler_api_php import call_api_php

# Inicializar colorama para colores en consola
init(autoreset=True)

# Carpetas de entrada y salida
INPUT_FOLDER = "1Inputs"
OUTPUT_FOLDER = "Publicar"
EXCLUSIONES_FOLDER = "xclusiones"
DEMO_MODE = False  # Determina si se activará el modo demo

def ensure_folders_exist():
    """
    Garantiza que las carpetas necesarias existan. Si no existen, las crea.
    """
    for folder in [INPUT_FOLDER, OUTPUT_FOLDER, EXCLUSIONES_FOLDER]:
        if not os.path.exists(folder):
            print(Fore.YELLOW + f"Creando carpeta: {folder}")
            os.makedirs(folder, exist_ok=True)
        else:
            print(Fore.GREEN + f"Carpeta '{folder}' encontrada.")

def cargar_exclusiones():
    """
    Carga todas las palabras clave de los archivos en la carpeta 'xclusiones'.
    Retorna un conjunto con las palabras clave.
    """
    exclusiones = set()
    if not os.listdir(EXCLUSIONES_FOLDER):
        print(Fore.RED + f"La carpeta '{EXCLUSIONES_FOLDER}' está vacía. No se aplicarán exclusiones.")
        return exclusiones

    for file in os.listdir(EXCLUSIONES_FOLDER):
        file_path = os.path.join(EXCLUSIONES_FOLDER, file)
        if os.path.isfile(file_path) and file.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    palabra = line.strip()
                    if palabra:
                        exclusiones.add(palabra.lower())
    print(Fore.GREEN + f"Exclusiones cargadas: {len(exclusiones)} palabras clave.")
    return exclusiones

def filtrar_emails(emails, exclusiones):
    """
    Filtra los correos electrónicos eliminando aquellos que contienen palabras clave en exclusiones.
    Muestra un mensaje fuerte en consola para cada email inválido detectado.
    """
    emails_validos = []
    for email in emails:
        if any(exclusion in email.lower() for exclusion in exclusiones):
            print(Fore.RED + f"EMAIL INVÁLIDO DETECTADO: {email}")
        else:
            emails_validos.append(email)
    return emails_validos

def display_menu():
    """
    Muestra un menú interactivo para elegir el modo de procesamiento.
    """
    global DEMO_MODE
    while True:
        print(Style.BRIGHT + Fore.CYAN + "\n============================================================")
        print("Seleccione el modo de procesamiento:")
        print("1. Procesar todos los registros (modo completo)")
        print("2. Procesar solo los primeros 20 registros (modo demo)")
        print("============================================================")
        choice = input(Fore.YELLOW + "Ingrese su elección (1 o 2): ").strip()

        if choice == "1":
            DEMO_MODE = False
            print(Fore.GREEN + "Procesamiento completo seleccionado.")
            break
        elif choice == "2":
            DEMO_MODE = True
            print(Fore.BLUE + "Modo demo seleccionado. Solo se procesarán 20 registros.")
            break
        else:
            print(Fore.RED + "Opción inválida. Por favor, ingrese '1' o '2'.")

def process_csv(file_path, exclusiones):
    """
    Procesa un archivo CSV y escribe los resultados en la carpeta 'Publicar'.
    """
    print(Fore.YELLOW + f"Procesando archivo: {file_path}")
    try:
        # Leer el CSV
        df = pd.read_csv(file_path)

        if "website" not in df.columns:
            print(Fore.RED + "El archivo no contiene una columna 'website'. Saltando...")
            return

        # Identificar las URLs válidas en la columna website
        valid_websites = []
        for index, website in enumerate(df["website"]):
            if isinstance(website, str) and website.strip():
                valid_websites.append((index, website.strip()))
            elif not pd.isna(website):
                print(Fore.RED + f" - Saltando fila {index}: Valor vacío o inválido en 'website'.")

        # Modo demo: limitar a 20 registros si está activado
        if DEMO_MODE:
            valid_websites = valid_websites[:20]
            print(Fore.BLUE + f"Modo demo activado. Procesando solo los primeros {len(valid_websites)} registros.")

        print(Fore.BLUE + "\nURLs a procesar:")
        for index, website in valid_websites:
            print(f" - Fila {index}: {website}")
        print(Fore.BLUE + f"Total URLs válidas a procesar: {len(valid_websites)}\n")

        if not valid_websites:
            print(Fore.RED + "No hay URLs válidas para procesar en este archivo.")
            return

        # Agregar columnas para los resultados sin eliminar las existentes
        social_columns = ["Instagram", "Facebook", "YouTube", "LinkedIn", "Twitter", "TikTok", "Pinterest"]
        new_columns = ["Emails"] + social_columns
        for col in new_columns:
            if col not in df.columns:
                df[col] = None  # Crear columnas nuevas si no existen

        # Procesar cada website válido
        for index, website in valid_websites:
            print(Fore.BLUE + f" - Llamando a la API para: {website}")
            api_response = call_api_php(website)

            # Obtener y filtrar emails
            emails = api_response.get("emails", [])
            emails_filtrados = filtrar_emails(emails, exclusiones)
            df.at[index, "Emails"] = ", ".join(emails_filtrados)

            # Obtener y agregar redes sociales
            social_links = api_response.get("social_links", {})
            for col in social_columns:
                links = social_links.get(col, [])
                df.at[index, col] = ", ".join(links)

        # Guardar el CSV procesado en la carpeta 'Publicar'
        output_file = os.path.join(OUTPUT_FOLDER, os.path.basename(file_path))
        df.to_csv(output_file, index=False)
        print(Fore.GREEN + f"Archivo procesado guardado en: {output_file}")

    except Exception as e:
        print(Fore.RED + f"Error procesando el archivo {file_path}: {e}")

def main():
    """
    Lee todos los archivos CSV de la carpeta '1Inputs' y los procesa.
    """
    print(Style.BRIGHT + Fore.CYAN + "============================================================")
    print("Inicio del procesamiento de CSVs")
    print("============================================================")

    # Asegurarse de que las carpetas existen
    ensure_folders_exist()

    # Cargar palabras clave de exclusión
    exclusiones = cargar_exclusiones()

    # Mostrar menú para seleccionar el modo
    display_menu()

    # Buscar todos los archivos CSV en la carpeta de entrada
    csv_files = glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))
    if not csv_files:
        print(Fore.RED + "No se encontraron archivos CSV en la carpeta '1Inputs'.")
        return

    for csv_file in csv_files:
        print(Style.BRIGHT + Fore.MAGENTA + f"\n------------------------------------------------------------")
        process_csv(csv_file, exclusiones)
        print(Style.BRIGHT + Fore.MAGENTA + "------------------------------------------------------------\n")

    print(Style.BRIGHT + Fore.CYAN + "============================================================")
    print("Procesamiento completado. Revisa los resultados en la carpeta 'Publicar'.")
    print("============================================================")

if __name__ == "__main__":
    main()
