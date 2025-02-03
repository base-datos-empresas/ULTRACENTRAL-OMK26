#!/usr/bin/env python3
"""
Publicador.py - Módulo para escribir archivos finales ordenados y optimizados.

Este módulo se encarga de guardar los archivos procesados y su versión demo
siguiendo un orden de prioridad para los usuarios, priorizando datos de contacto
seguido de filtros clave y metadatos menos relevantes al final.
"""

import os
import pandas as pd
from colorama import Fore, Style, init

# Inicializar colorama para mensajes en consola.
init(autoreset=True)

# Orden de columnas priorizado
COLUMN_ORDER = [
    "name", "main_category", "categories",
    "Emails", "phone", "website", "Instagram", "Facebook", "YouTube", "LinkedIn", "Twitter", "address",
    "rating", "reviews", "is_spending_on_ads", "competitors", "owner_name", "owner_profile_link",
    "workday_timing", "is_temporarily_closed", "closed_on", "can_claim",
    "link", "id"  # 'id' siempre al final
]

def guardar_archivos_finales(df: pd.DataFrame, base_name: str, output_folder: str) -> dict:
    """
    Guarda el DataFrame en formato CSV y Excel en la carpeta de salida y genera una versión demo ordenada.

    Args:
        df (pd.DataFrame): DataFrame a guardar.
        base_name (str): Nombre base para los archivos.
        output_folder (str): Carpeta donde se guardarán los archivos.

    Returns:
        dict: Diccionario con las rutas de los archivos generados:
            {
                'csv': ruta al archivo CSV procesado,
                'excel': ruta al archivo Excel procesado,
                'demo_csv': ruta al archivo CSV demo,
                'demo_excel': ruta al archivo Excel demo
            }
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        print(Fore.YELLOW + f"Carpeta de salida '{output_folder}' creada.")

    # Asegurar el orden de las columnas y eliminar 'query' si existe
    df = df.drop(columns=['query'], errors='ignore')
    if 'place_id' in df.columns:
        df = df.rename(columns={'place_id': 'id'})
    df = df[COLUMN_ORDER]

    # Definir rutas de los archivos procesados.
    csv_output_file = os.path.join(output_folder, f"{base_name}-Central-Completed.csv")
    excel_output_file = os.path.join(output_folder, f"{base_name}-Central-Completed.xlsx")

    # Guardar DataFrame en CSV y Excel con filtros en Excel.
    df.to_csv(csv_output_file, index=False)
    print(Fore.GREEN + f"Archivo CSV procesado guardado en: {csv_output_file}")

    with pd.ExcelWriter(excel_output_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=base_name)
        worksheet = writer.sheets[base_name]
        for col in worksheet.iter_cols():
            worksheet.auto_filter.ref = worksheet.dimensions
    print(Fore.GREEN + f"Archivo Excel procesado guardado en: {excel_output_file}")

    # Crear la versión demo del archivo.
    demo_csv_path, demo_excel_path = crear_version_demo(df, csv_output_file, base_name)

    return {
        'csv': csv_output_file,
        'excel': excel_output_file,
        'demo_csv': demo_csv_path,
        'demo_excel': demo_excel_path
    }

def crear_version_demo(df: pd.DataFrame, csv_output_file: str, base_name: str) -> (str, str):
    """
    Crea una versión demo del DataFrame en la cual se anonimicen columnas sensibles y se mantenga el orden adecuado.

    Args:
        df (pd.DataFrame): DataFrame original.
        csv_output_file (str): Ruta del archivo CSV procesado (se usa para derivar el nombre demo).
        base_name (str): Nombre base para la hoja en Excel.

    Returns:
        tuple: Rutas al archivo CSV demo y al archivo Excel demo.
    """
    # Copia del DataFrame para modificar la versión demo.
    demo_df = df.copy()

    # Anonimizar columnas sensibles.
    columns_to_anonymize = ["phone", "Emails", "website"]
    for col in columns_to_anonymize:
        if col in demo_df.columns:
            demo_df[col] = demo_df[col].apply(lambda x: "***" if pd.notna(x) else x)
            print(Fore.BLUE + f"Columna '{col}' anonimizada en la versión demo.")

    # Generar nombres de archivos demo basados en el nombre del archivo procesado.
    demo_csv_path = csv_output_file.replace("-Central-Completed", "-Central-Demo")
    demo_excel_path = demo_csv_path.replace(".csv", ".xlsx")

    # Guardar la versión demo en CSV y Excel con filtros en Excel.
    demo_df.to_csv(demo_csv_path, index=False)
    print(Fore.GREEN + f"Versión demo CSV guardada en: {demo_csv_path}")

    with pd.ExcelWriter(demo_excel_path, engine="openpyxl") as writer:
        demo_df.to_excel(writer, index=False, sheet_name=base_name)
        worksheet = writer.sheets[base_name]
        for col in worksheet.iter_cols():
            worksheet.auto_filter.ref = worksheet.dimensions
    print(Fore.GREEN + f"Versión demo Excel guardada en: {demo_excel_path}")

    return demo_csv_path, demo_excel_path
