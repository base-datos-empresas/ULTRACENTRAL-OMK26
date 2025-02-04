#!/usr/bin/env python3
"""
main.py - Procesador de CSV con validación de emails, API, síntesis de voz y enlaces clicables
pablo febrero
Este script se encarga de:
✔ Verificar y crear las carpetas necesarias.
✔ Cargar palabras clave de exclusión desde archivos .txt.
✔ Preguntar al usuario si desea activar la salida de voz.
✔ Mostrar un menú interactivo para elegir el modo de procesamiento.
✔ Leer archivos CSV, validar emails con ComprsobadorEmail.py y obtener información de la API.
✔ Guardar los resultados usando Publicador.py en CSV y Excel, incluyendo una versión demo.
✔ Mostrar enlaces clicables para abrir los archivos generados (recomendado en iTerm2).
✔ Proporcionar una experiencia visual y auditiva atractiva en consola con colores, banners mega, barras de progreso y mensajes hablados.
"""

import os
import glob
import pandas as pd
from colorama import Fore, Style, init
from tqdm import tqdm
import pyttsx3  # Biblioteca para síntesis de voz

# Inicializar colorama para colores en consola
init(autoreset=True)

# Inicializar el motor de voz
engine = pyttsx3.init()
SPEAK_ENABLED = False  # Por defecto desactivado; se preguntará al usuario


def speak(text):
    """Reproduce en voz alta el mensaje dado, si SPEAK_ENABLED es True."""
    if SPEAK_ENABLED:
        engine.say(text)
        engine.runAndWait()


def preguntar_voz():
    """Pregunta al usuario si desea activar la salida de voz."""
    global SPEAK_ENABLED
    respuesta = input(Fore.YELLOW + "¿Desea activar la voz? (S/N): ").strip().lower()
    if respuesta in ("s", "si"):
        SPEAK_ENABLED = True
        print(Fore.GREEN + "✅ Salida de voz activada.")
        speak("La salida de voz ha sido activada.")
    else:
        SPEAK_ENABLED = False
        print(Fore.BLUE + "🔹 Salida de voz desactivada.")


def make_clickable_link(file_path, display_text=None):
    """
    Devuelve un string con el enlace clicable para el archivo, utilizando secuencias OSC 8.

    Nota: Esto suele funcionar en terminales que soporten OSC 8 (por ejemplo, iTerm2 en macOS).

    Args:
        file_path (str): Ruta del archivo.
        display_text (str, opcional): Texto a mostrar. Si no se especifica, se usará la ruta.

    Returns:
        str: Cadena formateada como enlace clicable.
    """
    abs_path = os.path.abspath(file_path)
    if display_text is None:
        display_text = file_path
    # Usamos \033]8;;file://{ruta}\033\\ para iniciar y \033]8;;\033\\ para terminar
    return f'\033]8;;file://{abs_path}\033\\{display_text}\033]8;;\033\\'


# Importar módulos personalizados
from crawler_api_php import call_api_php  # Asegúrate de tener implementada esta función
import ComprobadorEmail  # Módulo para validar emails
import Publicador  # Módulo para guardar archivos finales (procesado y demo)

# Definir carpetas y configuraciones
INPUT_FOLDER = "1Inputs"
OUTPUT_FOLDER = "Publicar"
EXCLUSIONES_FOLDER = "xclusiones"
DEMO_MODE = False  # Modo demo: procesa solo 20 registros
VERBOSE = True  # Muestra mensajes de depuración extra


# ==========================================================
# FUNCIONES ESTÉTICAS PARA MEJORAR LA CONSOLA
# ==========================================================

def print_banner():
    """Muestra un banner MEGA llamativo al inicio del programa."""
    banner = f"""
{Style.BRIGHT}{Fore.MAGENTA}
  ███╗   ███╗███████╗ ██████╗ ██╗   ██╗███████╗██╗  ██╗     ██████╗ ███████╗██╗   ██╗
  ████╗ ████║██╔════╝██╔════╝ ██║   ██║██╔════╝██║  ██║    ██╔════╝ ██╔════╝██║   ██║
  ██╔████╔██║█████╗  ██║  ███╗██║   ██║█████╗  ███████║    ██║  ███╗█████╗  ██║   ██║
  ██║╚██╔╝██║██╔══╝  ██║   ██║██║   ██║██╔══╝  ██╔══██║    ██║   ██║██╔══╝  ██║   ██║
  ██║ ╚═╝ ██║███████╗╚██████╔╝╚██████╔╝███████╗██║  ██║    ╚██████╔╝██║     ╚██████╔╝
  ╚═╝     ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚═╝      ╚═════╝ 

██████╗ ███████╗███████╗██╗      █████╗ ██╗   ██╗██╗██████╗ 
██╔══██╗██╔════╝██╔════╝██║     ██╔══██╗██║   ██║██║██╔══██╗
██║  ██║█████╗  ███████╗██║     ███████║██║   ██║██║██║  ██║
██║  ██║██╔══╝  ╚════██║██║     ██╔══██║██║   ██║██║██║  ██║
██████╔╝███████╗███████║███████╗██║  ██║╚██████╔╝██║██████╔╝
╚═════╝ ╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═════╝ 

                🔥 Mega Procesador de CSV con Emails y API 🔥
---------------------------------------------------------------
{Style.RESET_ALL}
"""
    print(banner)
    speak("Bienvenido al Mega Procesador de CSV con Emails y API.")


def print_section(title):
    """Imprime una sección destacada con un título llamativo."""
    print(f"\n{Style.BRIGHT}{Fore.CYAN}🔹 {title} 🔹{Style.RESET_ALL}")
    speak(title)


# ==========================================================
# FUNCIONES PRINCIPALES
# ==========================================================

def ensure_folders_exist():
    """Verifica que existan las carpetas necesarias y las crea si no están presentes."""
    print_section("Verificando Carpetas Necesarias")
    for folder in [INPUT_FOLDER, OUTPUT_FOLDER, EXCLUSIONES_FOLDER]:
        if not os.path.exists(folder):
            print(Fore.YELLOW + f"📁 Creando carpeta: {folder}")
            os.makedirs(folder, exist_ok=True)
        else:
            print(Fore.GREEN + f"✔ Carpeta encontrada: {folder}")
    speak("Las carpetas necesarias han sido verificadas.")


def cargar_exclusiones():
    """Carga palabras clave de exclusión desde archivos en la carpeta EXCLUSIONES_FOLDER."""
    print_section("Cargando Palabras Clave de Exclusión")
    exclusiones = set()
    if not os.listdir(EXCLUSIONES_FOLDER):
        print(Fore.RED + "⚠ La carpeta de exclusiones está vacía. No se aplicarán filtros.")
        speak("Atención, la carpeta de exclusiones está vacía.")
        return exclusiones

    for file in os.listdir(EXCLUSIONES_FOLDER):
        file_path = os.path.join(EXCLUSIONES_FOLDER, file)
        if file.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    palabra = line.strip().lower()
                    if palabra:
                        exclusiones.add(palabra)
                        if VERBOSE:
                            print(Fore.BLUE + f"🔹 Exclusión cargada: {palabra}")
    print(Fore.GREEN + f"✔ Total exclusiones cargadas: {len(exclusiones)}")
    speak(f"Se han cargado {len(exclusiones)} exclusiones.")
    return exclusiones


def filtrar_emails(emails, exclusiones):
    """Filtra correos electrónicos usando ComprobadorEmail y exclusiones."""
    emails_validos = []
    print(Fore.CYAN + "Iniciando validación de correos electrónicos...")
    for email in emails:
        print(Fore.YELLOW + f"Procesando cadena de email: {email}")
        validos = ComprobadorEmail.validar_email(email)
        if not validos:
            print(Fore.RED + f"⚠ No se encontró email válido en: {email}")
        for v in validos:
            if any(exclusion in v.lower() for exclusion in exclusiones):
                print(Fore.RED + f"⛔ Email excluido (por exclusión): {v}")
            else:
                print(Fore.GREEN + f"✔ Email válido: {v}")
                emails_validos.append(v)
    print(Fore.CYAN + f"Total de emails válidos: {len(emails_validos)}")
    return emails_validos


def display_menu():
    """Muestra el menú para seleccionar el modo de procesamiento."""
    global DEMO_MODE
    while True:
        print_section("Seleccionar Modo de Procesamiento")
        print("1️⃣ Procesar todos los registros (modo completo)")
        print("2️⃣ Procesar solo los primeros 20 registros (modo demo)")
        choice = input(Fore.YELLOW + "👉 Ingrese su elección (1 o 2): ").strip()
        if choice == "1":
            DEMO_MODE = False
            print(Fore.GREEN + "✅ Procesamiento completo seleccionado.")
            speak("Modo completo seleccionado.")
            break
        elif choice == "2":
            DEMO_MODE = True
            print(Fore.BLUE + "🔹 Modo demo activado. Procesando solo 20 registros.")
            speak("Modo demo activado.")
            break
        else:
            print(Fore.RED + "⚠ Opción inválida. Intente nuevamente.")
            speak("Opción inválida, por favor intente nuevamente.")


def procesar_link(link):
    """
    Elimina de un enlace los prefijos 'https://www.' y 'https://' para obtener solo el dominio.
    """
    if link.startswith("https://www."):
        return link[len("https://www."):]
    elif link.startswith("https://"):
        return link[len("https://"):]
    return link


def process_csv(file_path, exclusiones):
    """Procesa un archivo CSV y guarda los resultados usando Publicador."""
    print_section(f"Procesando archivo: {file_path}")

    try:
        df = pd.read_csv(file_path)
        print(Fore.BLUE + f"✔ CSV cargado. Total de filas: {len(df)}")
    except Exception as e:
        print(Fore.RED + f"⚠ Error al leer el archivo CSV: {e}")
        speak("Error al leer el archivo CSV.")
        return

    if "website" not in df.columns:
        print(Fore.RED + "⚠ Archivo sin columna 'website'. Saltando...")
        speak("El archivo no contiene la columna website. Se omitirá este archivo.")
        return

    # Extraer URLs válidas de la columna 'website'
    valid_websites = [(i, w.strip()) for i, w in enumerate(df["website"]) if isinstance(w, str) and w.strip()]
    if DEMO_MODE:
        valid_websites = valid_websites[:20]

    # Definir las redes sociales que queremos procesar
    social_columns = ["Instagram", "Facebook", "YouTube", "LinkedIn", "Twitter", "TikTok", "Pinterest"]

    # Procesar cada website con barra de progreso
    for index, website in tqdm(valid_websites, desc="Procesando sitios web", unit="sitio"):
        try:
            api_response = call_api_php(website)
        except Exception as e:
            print(Fore.RED + f"⚠ Error llamando a la API para {website}: {e}")
            speak(f"Error llamando a la API para {website}.")
            api_response = {}  # Asignar diccionario vacío para continuar

        # Extraer y filtrar emails
        emails = api_response.get("emails", [])
        emails_filtrados = filtrar_emails(emails, exclusiones)
        df.at[index, "Emails"] = ", ".join(emails_filtrados)
        if emails_filtrados:
            mensaje = f"Para el sitio {website} se encontraron {len(emails_filtrados)} emails válidos."
            print(Fore.MAGENTA + mensaje)
            speak(mensaje)

        # Procesar redes sociales (si existen)
        social_links_dict = api_response.get("social_links", {})
        for col in social_columns:
            links = social_links_dict.get(col, [])
            if links:
                df.at[index, col] = ", ".join(links)
                # Procesar cada enlace para eliminar los prefijos antes de hablar
                processed_links = [procesar_link(link) for link in links]
                # Formar el mensaje sin listar literalmente la URL completa
                mensaje_social = f"El sitio {website} tiene en {col}: {', '.join(processed_links)}."
                print(Fore.MAGENTA + mensaje_social)
                speak(mensaje_social)

    # Construir nombre base para guardar archivos
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    print(Fore.CYAN + f"Llamando a Publicador para guardar archivos finales usando base: '{base_name}'")
    speak(f"Guardando resultados para {base_name}.")
    resultados = Publicador.guardar_archivos_finales(df, base_name, OUTPUT_FOLDER)

    print_section("Archivos Generados")
    # Mostrar enlaces clicables para cada archivo generado
    for key, path in resultados.items():
        clickable = make_clickable_link(path, f"{key}: {path}")
        print(Fore.GREEN + f"✔ {clickable}")
    speak("El archivo ha sido guardado correctamente.")


def main():
    """Función principal que orquesta todo el proceso."""
    print_banner()
    preguntar_voz()  # Preguntar al usuario si desea salida de voz
    ensure_folders_exist()
    exclusiones = cargar_exclusiones()
    display_menu()

    csv_files = glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))
    if not csv_files:
        print(Fore.RED + "⚠ No se encontraron archivos CSV en '1Inputs'.")
        speak("No se encontraron archivos CSV en la carpeta de entrada.")
        return

    print_section(f"Se encontraron {len(csv_files)} archivos CSV")
    speak(f"Se encontraron {len(csv_files)} archivos CSV para procesar.")
    for csv_file in csv_files:
        process_csv(csv_file, exclusiones)

    print(Fore.GREEN + "\n🎉 ¡Procesamiento completado! Revisa la carpeta 'Publicar'.\n")
    speak("Procesamiento completado. Revisa la carpeta Publicar.")


if __name__ == "__main__":
    main()
