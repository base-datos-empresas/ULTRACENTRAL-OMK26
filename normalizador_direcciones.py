#!/usr/bin/env python3
import re
import json
import os
import requests

# Ruta del archivo donde se almacenan los formatos aprendidos
FORMATOS_FILE = "formatos_direcciones.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


# Cargar patrones aprendidos desde JSON
def cargar_formatos():
    if os.path.exists(FORMATOS_FILE):
        with open(FORMATOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# Guardar patrones aprendidos en JSON
def guardar_formatos(formatos):
    with open(FORMATOS_FILE, "w", encoding="utf-8") as f:
        json.dump(formatos, f, indent=4, ensure_ascii=False)


# Consultar OpenStreetMap (OSM) si el patrón no es conocido
def query_osm_nominatim(address):
    try:
        params = {
            "q": address,
            "format": "json",
            "addressdetails": 1,
            "limit": 1,
        }
        response = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": "CentralCompanies/1.0"})
        response.raise_for_status()
        data = response.json()

        if not data:
            return None, None, None, None, None

        address_data = data[0]["address"]
        street = address_data.get("road", "")
        postal_code = address_data.get("postcode", "")
        locality = address_data.get("city", address_data.get("town", address_data.get("village", "")))
        province = address_data.get("state", "")
        country = address_data.get("country_code", "").upper()

        return street, postal_code, locality, province, country

    except requests.RequestException as e:
        print(f"Error en OpenStreetMap: {e}")
        return None, None, None, None, None


# Intentar normalizar con un patrón conocido
def parse_address_with_pattern(address, pattern_data):
    match = re.match(pattern_data["pattern"], address.strip())
    if match:
        values = match.groups()
        parsed_data = {key: values[i] for i, key in enumerate(pattern_data["groups"])}
        return parsed_data
    return None


# Aprender un nuevo patrón a partir de los datos de OpenStreetMap
def aprender_nuevo_formato(address, country_code, osm_data, formatos):
    street, postal_code, locality, province, country = osm_data
    if not all([street, postal_code, locality, province]):
        return False  # No hay suficientes datos para crear un patrón

    # Crear un nuevo patrón basado en la estructura de la dirección
    new_pattern = re.escape(street) + r",?\s*" + re.escape(postal_code) + r"\s+" + re.escape(
        locality) + r",\s*" + re.escape(province)

    formatos[country_code] = {
        "pattern": new_pattern,
        "groups": ["street", "postal_code", "locality", "province"]
    }
    guardar_formatos(formatos)
    print(f"Nuevo formato aprendido para {country_code}: {new_pattern}")
    return True


# Función principal que intenta normalizar una dirección con patrones aprendidos o OSM
def parse_address_by_country(address, country_code):
    formatos = cargar_formatos()
    country_code = country_code.upper()

    # Intentar usar un patrón aprendido previamente
    if country_code in formatos:
        parsed_data = parse_address_with_pattern(address, formatos[country_code])
        if parsed_data:
            return parsed_data["street"], parsed_data["postal_code"], parsed_data["locality"], parsed_data[
                "province"], country_code

    # Si no hay patrón, consultar OpenStreetMap
    print(f"Consultando OpenStreetMap para mejorar la dirección: {address}")
    osm_data = query_osm_nominatim(address)

    if osm_data and any(osm_data):
        # Intentar aprender el nuevo formato
        if aprender_nuevo_formato(address, country_code, osm_data, formatos):
            return osm_data
        else:
            return osm_data  # Devolver datos sin aprendizaje

    # Si no se encontró nada, devolver la dirección sin procesar
    return address, "", "", "", country_code
