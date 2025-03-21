#!/usr/bin/env python3
import requests
from colorama import Fore

PHP_API_URL = "https://centralapi.site/apiemailsocial.php"

def call_api_php(domain):
    """
    Llama a la API PHP para el dominio dado y devuelve los resultados JSON.
    """
    try:
        print(Fore.YELLOW + f"🌐 Llamando a la API para {domain} ...")
        response = requests.get(PHP_API_URL, params={"domain": domain}, timeout=15)
        response.raise_for_status()
        data = response.json()
        print(Fore.GREEN + "✅ Respuesta recibida de la API.")
        return data
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"❌ Error al llamar a la API: {e}")
        return {"error": True, "message": str(e)}
    except ValueError:
        print(Fore.RED + "❌ Error interpretando la respuesta de la API como JSON.")
        return {"error": True, "message": "Invalid JSON response"}
