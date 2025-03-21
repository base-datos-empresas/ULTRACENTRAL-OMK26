#!/usr/bin/env python3
import os
import pandas as pd
from colorama import Fore
from openpyxl import Workbook

# Importamos la función que normaliza direcciones
from normalizador_direcciones import parse_address_by_country

# -------------------------------------------------------------
# ORDEN DE COLUMNAS PARA AMBAS VERSIONES (COMPLETA Y DEMO)
# -------------------------------------------------------------
COLUMN_ORDER = [
    "name", "main_category", "categories",
    "Emails", "phone", "website", "Instagram", "Facebook", "YouTube",
    "LinkedIn", "Twitter", "address",  # Mantén 'address' si deseas la columna original
    "street", "postal_code", "locality", "province", "country",
    "rating", "reviews", "is_spending_on_ads", "competitors", "owner_name",
    "owner_profile_link", "workday_timing", "is_temporarily_closed",
    "closed_on", "can_claim", "link", "id"
]

# -------------------------------------------------------------
# TEXTO LEGAL O COPYRIGHT PARA LA PESTAÑA CORRESPONDIENTE
# -------------------------------------------------------------
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

def generate_statistics_en(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea un DataFrame con estadísticas en inglés:
      - Number of companies
      - Number of phones
      - Number of emails
    """
    num_companies = len(df)

    num_phones = 0
    if "phone" in df.columns:
        num_phones = (
            df["phone"].astype(str).str.strip()
            .replace("", pd.NA).dropna().shape[0]
        )

    total_emails = 0
    if "Emails" in df.columns:
        for val in df["Emails"].dropna():
            splitted = [email.strip() for email in str(val).split(",") if email.strip()]
            total_emails += len(splitted)

    data = {
        "Metric": [
            "Number of companies",
            "Number of phones",
            "Number of emails"
        ],
        "Value": [
            num_companies,
            num_phones,
            total_emails
        ]
    }
    return pd.DataFrame(data)

def generate_sectors_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna un DF con 'Sector' y 'Count', basado en la columna 'main_category'.
    Ordenado de mayor a menor.
    """
    if "main_category" not in df.columns:
        return pd.DataFrame({"Sector": [], "Count": []})

    counts = df["main_category"].dropna().value_counts()
    sectors_df = counts.reset_index()
    sectors_df.columns = ["Sector", "Count"]
    return sectors_df

def anonymize_data(value):
    """
    Anonimiza datos en columnas sensibles (phone, Emails, website).
    """
    return "***" if pd.notna(value) else value

def crear_version_demo(original_df: pd.DataFrame, csv_output_file: str, base_name: str):
    """
    Crea la VERSIÓN DEMO del DataFrame (CSV y Excel con 4 pestañas).
    1. Anonimiza phone, Emails, website.
    2. Mantiene o no las direcciones (depende de si deseas anonimizar 'address' o 'street').
    3. Reemplaza '-CentralCompanies' por '-CentralDemo' en el nombre de salida.
    """
    demo_df = original_df.copy()

    # Anonimizar columnas sensibles
    for col in ["phone", "Emails", "website"]:
        if col in demo_df.columns:
            demo_df[col] = demo_df[col].apply(anonymize_data)

    # (Opcional) anonimizar address/street si también quieres ocultar direcciones
    # for col in ["address", "street"]:
    #     if col in demo_df.columns:
    #         demo_df[col] = demo_df[col].apply(anonymize_data)

    demo_csv_path = csv_output_file.replace("-CentralCompanies", "-CentralDemo")
    demo_excel_path = demo_csv_path.replace(".csv", ".xlsx")

    # Generar DataFrames auxiliares
    stats_demo = generate_statistics_en(demo_df)
    sectors_demo = generate_sectors_df(demo_df)
    copyright_df = pd.DataFrame({
        "Copyright": COPYRIGHT_TEXT
    })

    # Guardar CSV DEMO
    demo_df.to_csv(demo_csv_path, index=False)
    print(Fore.GREEN + f"Versión DEMO (CSV): {demo_csv_path}")

    # Guardar Excel DEMO
    with pd.ExcelWriter(demo_excel_path, engine="openpyxl") as writer:
        demo_df.to_excel(writer, sheet_name="Data", index=False)
        stats_demo.to_excel(writer, sheet_name="Statistics", index=False)
        sectors_demo.to_excel(writer, sheet_name="Sectors", index=False)
        copyright_df.to_excel(writer, sheet_name="Copyright", index=False)

    print(Fore.GREEN + f"Versión DEMO (Excel): {demo_excel_path}")
    return demo_csv_path, demo_excel_path

def guardar_archivos_finales(df: pd.DataFrame, base_name: str, output_folder: str) -> dict:
    """
    Genera:
      1) Versión COMPLETA (CSV y Excel con 4 pestañas)
      2) Versión DEMO (CSV y Excel con 4 pestañas), anonimizando phone/Emails/website
    EN ADEMÁS: Normaliza la dirección con 'parse_address_by_country' (de normalizador_direcciones)
    para obtener columnas: street, postal_code, locality, province, country.

    Retorna un dict con las rutas:
      {
        "csv_completo":  <ruta CSV completo>,
        "excel_completo": <ruta Excel completo>,
        "demo_csv": <ruta CSV demo>,
        "demo_excel": <ruta Excel demo>
      }
    """
    from normalizador_direcciones import parse_address_by_country

    # Crear subcarpeta según el prefijo de país
    country_initials = base_name.split("-")[0].upper()
    country_folder = os.path.join(output_folder, country_initials)
    os.makedirs(country_folder, exist_ok=True)
    print(Fore.YELLOW + f"Carpeta para país '{country_initials}': {country_folder}")

    # Eliminar columnas que no queremos
    if "query" in df.columns:
        df.drop(columns=["query"], inplace=True, errors="ignore")
    if "place_id" in df.columns:
        df.rename(columns={"place_id": "id"}, inplace=True)

    # Normalizar direcciones si existe la columna 'address'
    if "address" in df.columns:
        # Llamamos a parse_address_by_country para cada valor
        parsed_info = df["address"].apply(lambda x: parse_address_by_country(x, country_initials))
        df["street"]      = parsed_info.apply(lambda x: x[0])
        df["postal_code"] = parsed_info.apply(lambda x: x[1])
        df["locality"]    = parsed_info.apply(lambda x: x[2])
        df["province"]    = parsed_info.apply(lambda x: x[3])
        # El quinto valor es el country_code, lo guardamos en 'country'
        df["country"]     = parsed_info.apply(lambda x: x[4])

    # Reordenar columnas
    df = df.reindex(columns=[col for col in COLUMN_ORDER if col in df.columns], fill_value="")

    # Rutas de salida
    csv_output_file = os.path.join(country_folder, f"{base_name}-CentralCompanies.csv")
    excel_output_file = csv_output_file.replace(".csv", ".xlsx")

    # GUARDAR CSV COMPLETO
    df.to_csv(csv_output_file, index=False)
    print(Fore.GREEN + f"CSV COMPLETO: {csv_output_file}")

    # Construir DataFrames auxiliares
    stats_df = generate_statistics_en(df)
    sectors_df = generate_sectors_df(df)
    copyright_df = pd.DataFrame({
        "Copyright": COPYRIGHT_TEXT
    })

    # GUARDAR EXCEL COMPLETO
    with pd.ExcelWriter(excel_output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
        stats_df.to_excel(writer, sheet_name="Statistics", index=False)
        sectors_df.to_excel(writer, sheet_name="Sectors", index=False)
        copyright_df.to_excel(writer, sheet_name="Copyright", index=False)

    print(Fore.GREEN + f"EXCEL COMPLETO: {excel_output_file}")

    # CREAR VERSIÓN DEMO
    demo_csv, demo_excel = crear_version_demo(df, csv_output_file, base_name)

    return {
        "csv_completo": csv_output_file,
        "excel_completo": excel_output_file,
        "demo_csv": demo_csv,
        "demo_excel": demo_excel
    }
