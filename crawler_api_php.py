#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from colorama import Fore

PHP_API_URL = "https://centralapi.site/apiemailsocial.php"

def call_api_php(domain):
    """
    Llama a la API PHP para el dominio dado y devuelve los resultados.
    """
    try:
        print(Fore.YELLOW + f"Realizando petición a la API para el dominio: {domain}")
        response = requests.get(PHP_API_URL, params={"domain": domain}, timeout=15)
        response.raise_for_status()
        data = response.json()
        print(Fore.GREEN + "Respuesta recibida de la API.")
        return data
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"Error llamando a la API: {e}")
        return {"error": True, "message": str(e)}
    except ValueError:
        print(Fore.RED + "Error interpretando la respuesta de la API como JSON.")
        return {"error": True, "message": "Invalid JSON response"}
