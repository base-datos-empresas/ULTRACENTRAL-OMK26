#!/usr/bin/env python3
import concurrent.futures
from crawler_api_php import call_api_php
from email_utils import filtrar_emails


def process_single_website(args):
    """
    Llama a la API PHP para un sitio web y filtra los emails retornados,
    además de extraer redes sociales.

    Args:
        args (tuple): (index, website, exclusiones)

    Returns:
        tuple: (index, emails_filtrados, social_data)
    """
    index, website, exclusiones = args
    api_response = call_api_php(website)

    emails = api_response.get("emails", [])
    emails_filtrados = filtrar_emails(emails, exclusiones)

    social_columns = ["Instagram", "Facebook", "YouTube", "LinkedIn", "Twitter", "TikTok", "Pinterest"]
    social_data = {
        col: ", ".join(api_response.get("social_links", {}).get(col, []))
        for col in social_columns
    }

    return index, emails_filtrados, social_data


def run_parallel_api(valid_websites, exclusiones, max_workers=10):
    """
    Ejecuta en paralelo el proceso de llamadas a la API para un conjunto de sitios web.

    Args:
        valid_websites (list): Lista de tuplas (index, website)
        exclusiones (set): Palabras clave para filtrar correos
        max_workers (int): Máximo número de hilos en el ThreadPool

    Returns:
        list: Lista de tuplas (index, emails_filtrados, social_data)
    """
    tasks = [(idx, web, exclusiones) for idx, web in valid_websites]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Puedes generar la lista directamente con list(...) o en un bucle, ambas funcionan
        results = list(executor.map(process_single_website, tasks))

    return results
