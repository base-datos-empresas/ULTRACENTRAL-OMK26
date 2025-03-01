import os
import glob
import json
import re
import pandas as pd
import dns.resolver
from email_validator import validate_email, EmailNotValidError
from colorama import Fore, Style, init
from crawler_api_php import call_api_php
import concurrent.futures

# Inicializar colorama para colores en consola
init(autoreset=True)

# Carpetas de entrada y salida
INPUT_FOLDER = "1Inputs"
OUTPUT_FOLDER = "Publicar"
EXCLUSIONES_FOLDER = "xclusiones"
PROGRESS_FILE = "progress_state.json"

# Modo demo (se selecciona en el menú interactivo)
DEMO_MODE = False

# Texto legal en inglés para la tercera pestaña, renombrado a "Copyright"
COPYRIGHT_TEXT = [
    "Legal Notice",
    "",
    "© companiesdata.cloud. All rights reserved.",
    "Registered with the Department of Culture and Historical Heritage GR-00416-2020.",
    "https://companiesdata.cloud/",
    "",
    "The sources of the data are the official websites of each company.",
    "We do not handle personal data, therefore LOPD or GDPR do not apply.",
    "",
    "The database is non-transferable and cannot be replicated.",
    "Copying, distribution, or partial or complete publication without express consent is prohibited.",
    "Legal measures will be taken for copyright infringements.",
    "",
    "For more information, please consult our Frequently Asked Questions:",
    "https://companiesdata.cloud/faq",
    "",
    "Reproduction, distribution, public communication, and transformation, in whole or in part,",
    "of the contents of this database is prohibited without the express authorization of companiesdata.cloud.",
    "The data has been collected from public sources and complies with current regulations."
]


###############################################################################
# Función para validar el email (formato y existencia de registros DNS)
###############################################################################
def validate_email_address(email):
    """
    Valida el formato del email y consulta registros DNS (MX o A) del dominio.
    Retorna (True, mensaje) si es válido o (False, mensaje) en caso contrario.
    """
    try:
        # Validación de formato con email_validator
        valid = validate_email(email)
        # Acceder al email validado usando el atributo recomendado
        email = valid.email
    except EmailNotValidError as e:
        return False, f"Formato inválido: {str(e)}"

    # Extraer dominio
    try:
        domain = email.split('@')[-1]
    except Exception:
        return False, "No se pudo extraer el dominio"

    # Consultar registros MX
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        if answers:
            return True, "Email válido (MX encontrado)"
    except Exception:
        pass

    # Si no hay MX, intentar consultar registros A
    try:
        answers = dns.resolver.resolve(domain, 'A')
        if answers:
            return True, "Email válido (A encontrado)"
    except Exception:
        return False, "No se encontraron registros MX ni A para el dominio"

    return False, "Validación DNS fallida"


###############################################################################
# Funciones del script de procesamiento CSV
###############################################################################
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
    Filtra los correos electrónicos eliminando aquellos que contienen palabras clave
    y aquellos que no pasan la validación (formato y DNS).
    Muestra un mensaje en consola para cada email inválido detectado.
    """
    emails_validos = []
    for email in emails:
        # Excluir si contiene alguna palabra clave
        if any(exclusion in email.lower() for exclusion in exclusiones):
            print(Fore.RED + f"EMAIL INVÁLIDO DETECTADO (exclusión): {email}")
            continue

        # Validar formato y registros DNS
        is_valid, msg = validate_email_address(email)
        if not is_valid:
            print(Fore.RED + f"EMAIL INVÁLIDO (validación fallida: {msg}): {email}")
            continue

        emails_validos.append(email)
    return emails_validos


def anonymize_data(value):
    """
    Reemplaza el valor con asteriscos para anonimizarlo.
    """
    return "***" if pd.notna(value) else value


def generate_statistics(df):
    """
    Genera un DataFrame con estadísticas basadas en el DataFrame procesado.
    Estadísticas:
      - Número de empresas (filas)
      - Número de teléfonos válidos (columna 'phone')
      - Número total de emails (columna 'Emails', contando cada email separado por coma)
      - Listado de categorías únicas (columna 'category', si existe)
    """
    num_empresas = len(df)

    num_telefonos = 0
    if "phone" in df.columns:
        num_telefonos = df["phone"].astype(str).str.strip().replace("", pd.NA).dropna().shape[0]

    total_emails = 0
    if "Emails" in df.columns:
        for entry in df["Emails"].dropna():
            emails_list = [email.strip() for email in str(entry).split(",") if email.strip() != ""]
            total_emails += len(emails_list)

    if "category" in df.columns:
        categorias = df["category"].dropna().unique().tolist()
    else:
        categorias = []

    stats = {
        "Estadística": [
            "Número de empresas",
            "Número de teléfonos",
            "Número de emails",
            "Listado de categorías"
        ],
        "Valor": [
            num_empresas,
            num_telefonos,
            total_emails,
            ", ".join(categorias) if categorias else "N/A"
        ]
    }
    return pd.DataFrame(stats)


def create_demo_version(df, output_path):
    """
    Crea una versión demo de un DataFrame, guardando un CSV y un Excel con tres pestañas:
    Datos, Estadísticas y Copyright.
    """
    demo_df = df.copy()

    # Renombrar la columna place_id a id si existe
    if "place_id" in demo_df.columns:
        demo_df.rename(columns={"place_id": "id"}, inplace=True)

    # Anonimizar las columnas phone, Emails y website
    for col in ["phone", "Emails", "website"]:
        if col in demo_df.columns:
            demo_df[col] = demo_df[col].apply(anonymize_data)

    demo_path_csv = output_path.replace("-Central-Completed", "-Central-Demo")
    demo_path_excel = demo_path_csv.replace(".csv", ".xlsx")

    # Guardar CSV (solo datos, ya que CSV no soporta pestañas)
    demo_df.to_csv(demo_path_csv, index=False)
    print(Fore.GREEN + f"Archivo demo CSV guardado en: {demo_path_csv}")

    # Guardar Excel con tres pestañas: Datos, Estadísticas y Copyright
    with pd.ExcelWriter(demo_path_excel, engine="openpyxl") as writer:
        demo_df.to_excel(writer, index=False, sheet_name="Datos")
        stats_df = generate_statistics(demo_df)
        stats_df.to_excel(writer, index=False, sheet_name="Estadísticas")
        copyright_df = pd.DataFrame({"Copyright": COPYRIGHT_TEXT})
        copyright_df.to_excel(writer, index=False, sheet_name="Copyright")
    print(Fore.GREEN + f"Archivo demo Excel guardado en: {demo_path_excel}")


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


def load_progress():
    """
    Carga el estado de progreso desde el archivo, si existe.
    """
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress):
    """
    Guarda el estado de progreso en el archivo.
    """
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=4)


def clear_progress():
    """
    Elimina el archivo de progreso cuando la tarea se completa.
    """
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)


###############################################################################
# Procesamiento en paralelo: función para procesar una sola URL
###############################################################################
def process_single_website(args):
    """
    Procesa una única URL:
      - Llama a la API para obtener información.
      - Filtra los emails y obtiene los datos de redes sociales.
    Retorna una tupla: (índice, emails filtrados, diccionario con redes sociales).
    """
    index, website, exclusiones = args
    api_response = call_api_php(website)
    emails = api_response.get("emails", [])
    emails_filtrados = filtrar_emails(emails, exclusiones)
    social_columns = ["Instagram", "Facebook", "YouTube", "LinkedIn", "Twitter", "TikTok", "Pinterest"]
    social_data = {}
    for col in social_columns:
        links = api_response.get("social_links", {}).get(col, [])
        social_data[col] = ", ".join(links)
    return index, emails_filtrados, social_data


def process_csv(file_path, exclusiones, progress):
    """
    Procesa un archivo CSV y escribe los resultados en la carpeta 'Publicar'.
    Implementa un checkpoint para reanudar el procesamiento en caso de interrupciones.
    Además, genera un archivo Excel con tres pestañas: Datos, Estadísticas y Copyright.
    """
    base_name = os.path.basename(file_path)
    file_progress = progress.get(base_name, {"last_index": -1})
    last_index = file_progress.get("last_index", -1)

    print(Fore.YELLOW + f"Procesando archivo: {file_path}")
    try:
        df = pd.read_csv(file_path)

        if "website" not in df.columns:
            print(Fore.RED + "El archivo no contiene una columna 'website'. Saltando...")
            return

        valid_websites = []
        for index, website in enumerate(df["website"]):
            if isinstance(website, str) and website.strip():
                valid_websites.append((index, website.strip()))
            elif not pd.isna(website):
                print(Fore.RED + f" - Saltando fila {index}: Valor vacío o inválido en 'website'.")

        if DEMO_MODE:
            valid_websites = valid_websites[:20]
            print(Fore.BLUE + f"Modo demo activado. Procesando solo los primeros {len(valid_websites)} registros.")

        total = len(valid_websites)
        print(Fore.BLUE + "\nURLs a procesar:")
        for pos, (index, website) in enumerate(valid_websites, start=1):
            print(f" - Registro {pos}/{total} (fila {index}): {website}")
        print(Fore.BLUE + f"Total URLs válidas a procesar: {total}\n")

        if not valid_websites:
            print(Fore.RED + "No hay URLs válidas para procesar en este archivo.")
            return

        # Preparar tareas para procesar en paralelo (solo registros nuevos)
        tasks = [(index, website, exclusiones) for (index, website) in valid_websites if index > last_index]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(process_single_website, tasks))

        for pos, (index, emails_filtrados, social_data) in enumerate(results, start=1):
            df.at[index, "Emails"] = ", ".join(emails_filtrados)
            for col, links in social_data.items():
                df.at[index, col] = links
            file_progress["last_index"] = index
            progress[base_name] = file_progress
            save_progress(progress)
            print(Fore.CYAN + f"Progreso: Registro (fila {index}) completado. {pos} de {total} procesados.\n")

        if "query" in df.columns:
            df.drop(columns=["query"], inplace=True)

        base_output = os.path.splitext(base_name)[0]
        csv_output_file = os.path.join(OUTPUT_FOLDER, f"{base_output}-Central-Completed.csv")
        excel_output_file = os.path.join(OUTPUT_FOLDER, f"{base_output}-Central-Completed.xlsx")

        df.to_csv(csv_output_file, index=False)
        print(Fore.GREEN + f"Archivo CSV procesado guardado en: {csv_output_file}")

        with pd.ExcelWriter(excel_output_file, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Datos")
            stats_df = generate_statistics(df)
            stats_df.to_excel(writer, index=False, sheet_name="Estadísticas")
            copyright_df = pd.DataFrame({"Copyright": COPYRIGHT_TEXT})
            copyright_df.to_excel(writer, index=False, sheet_name="Copyright")
        print(Fore.GREEN + f"Archivo Excel procesado guardado en: {excel_output_file}")

        create_demo_version(df, csv_output_file)

    except Exception as e:
        print(Fore.RED + f"Error procesando el archivo {file_path}: {e}")


def main():
    """
    Lee todos los archivos CSV de la carpeta '1Inputs' y los procesa.
    Incorpora un mecanismo de checkpointing para reanudar tareas pendientes y muestra el progreso en pantalla.
    """
    print(Style.BRIGHT + Fore.CYAN + "============================================================")
    print("Inicio del procesamiento de CSVs")
    print("============================================================")

    ensure_folders_exist()
    exclusiones = cargar_exclusiones()
    display_menu()

    progress = load_progress()
    if progress:
        respuesta = input("Se detectó una tarea pendiente. ¿Desea continuar desde donde quedó? (s/n): ").strip().lower()
        if respuesta != "s":
            progress = {}
            clear_progress()
            print("Iniciando una nueva tarea desde cero.")
        else:
            print("Reanudando la tarea pendiente...")

    csv_files = glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))
    if not csv_files:
        print(Fore.RED + "No se encontraron archivos CSV en la carpeta '1Inputs'.")
        return

    for csv_file in csv_files:
        print(Style.BRIGHT + Fore.MAGENTA + "\n------------------------------------------------------------")
        process_csv(csv_file, exclusiones, progress)
        print(Style.BRIGHT + Fore.MAGENTA + "------------------------------------------------------------\n")

    clear_progress()
    print(Style.BRIGHT + Fore.CYAN + "============================================================")
    print("Procesamiento completado. Revisa los resultados en la carpeta 'Publicar'.")
    print("============================================================")


if __name__ == "__main__":
    main()
