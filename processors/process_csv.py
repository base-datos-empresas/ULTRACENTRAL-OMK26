#!/usr/bin/env python3
import os
import pandas as pd
from colorama import Fore
# Import relativo: parallel_api.py está en la misma carpeta 'processors'
from .parallel_api import run_parallel_api
# Import de 'Publicador.py' (ubicado en la raíz del proyecto, o en el PYTHONPATH)
from Publicador import guardar_archivos_finales

def process_csv(file_path, exclusiones, demo_mode=False):
    """
    Procesa un archivo CSV:
      - Lee el CSV y verifica que exista la columna 'website'.
      - Prepara una lista de sitios web válidos (limpia los vacíos).
      - Si está en modo demo, se queda con los primeros 20 registros.
      - Llama a 'run_parallel_api' para extraer correos y redes sociales en paralelo.
      - Actualiza las columnas 'Emails' y redes sociales en el DataFrame.
      - Finalmente, invoca 'guardar_archivos_finales' para guardar el DataFrame en la carpeta de salida.
    """
    base_name = os.path.basename(file_path).replace(".csv", "")
    print(Fore.YELLOW + f"📄 Procesando archivo: {file_path}")

    try:
        df = pd.read_csv(file_path)
        if "website" not in df.columns:
            print(Fore.RED + f"⚠ Archivo sin 'website'. Saltando...")
            return

        # Extraer los sitios web válidos (que no sean NaN ni cadenas vacías)
        valid_websites = [
            (idx, site.strip())
            for idx, site in df["website"].dropna().items()
            if site.strip()
        ]

        if demo_mode:
            # Limitar a 20 registros si es modo demo
            valid_websites = valid_websites[:20]
            print(Fore.BLUE + f"🔹 Modo demo activado. Procesando {len(valid_websites)} registros.")

        if not valid_websites:
            print(Fore.RED + "🚨 No hay URLs válidas para procesar en este archivo.")
            return

        # Llamamos a la ejecución en paralelo para obtener emails y redes sociales
        results = run_parallel_api(valid_websites, exclusiones)

        # Actualizamos el DataFrame con los datos recibidos
        for index, emails_filtrados, social_data in results:
            df.at[index, "Emails"] = ", ".join(emails_filtrados)
            for col, links in social_data.items():
                df.at[index, col] = links

        # Publicamos (guardamos) el DataFrame final en la carpeta de salida
        guardar_archivos_finales(df, base_name, "Publicar")

    except Exception as e:
        print(Fore.RED + f"❌ ERROR procesando {file_path}: {e}")
