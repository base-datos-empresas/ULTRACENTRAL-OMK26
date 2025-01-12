#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
import time
import sys
import json
import select
from urllib.parse import urljoin, urlparse
from collections import deque

# Configuración del crawler
MAX_DOWNLOAD_SIZE = 2 * 1024 * 1024  # 2 MB
MAX_PAGES = 50
MAX_DEPTH = 2
MAX_CHILD_LINKS = 10
REQUEST_TIMEOUT = 15  # segundos de timeout para la petición HTTP

# Expresiones regulares (SIN grupos de captura) para redes sociales
SOCIAL_REGEX = {
    'Instagram': r'https?:\/\/(?:www\.)?instagram\.com\/(?!about|explore|developer|legal|press|privacy|terms|accounts|directory|p\/|reel\/|stories\/)[A-Za-z0-9_.]{1,30}(?:\/)?',
    'Facebook':  r'https?:\/\/(?:[a-z0-9-]+\.)*facebook\.com\/(?!pages|groups|events|help|policies|marketplace|watch|live|settings|messages|notifications|bookmarks|memories|fundraisers|games|jobs|privacy|terms|login|dialog|plugins|tr\/?|sharer(?:\.php)?\/?)[A-Za-z0-9.]{5,50}(?:\/)?',
    'YouTube':   r'https?:\/\/(?:www\.)?youtube\.com\/(?:c\/|channel\/|user\/|@)[A-Za-z0-9_\-]{1,50}(?:\/)?',
    'LinkedIn':  r'https?:\/\/(?:[a-z]{2,3}\.)?linkedin\.com\/(?:company\/|in\/)[A-Za-z0-9_\-]{1,50}(?:\/)?',
    'Twitter':   r'https?:\/\/(?:www\.)?(?:x\.com|twitter\.com)\/(?!home|explore|notifications|messages|intent|share|search)[A-Za-z0-9_]{1,15}(?:\/)?',
    'TikTok':    r'https?:\/\/(?:www\.)?tiktok\.com\/@(?!live|discover|tag|music|video)[A-Za-z0-9_.\-]{1,24}(?:\/)?',
    'Pinterest': r'https?:\/\/(?:www\.)?pinterest\.com\/(?!pin|explore|topics|login|signup|categories|about)[A-Za-z0-9_.\-\/]+'
}

# Expresión regular para correos electrónicos (sin grupos de captura)
EMAIL_REGEX = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'

# Palabras clave para excluir correos electrónicos
EXCLUDE_WORDS = ['legal', 'datos', 'proteccion', 'lopd', 'rgpd', 'png']


def clean_url(url: str) -> str:
    """
    Limpia y valida la URL, forzando 'http://' si no existe esquema.
    Devuelve la URL normalizada o None si no es válida.
    """
    if not url or url.strip() == '':
        return None

    url = url.strip()

    # Añadir el esquema si no está presente
    if not re.match(r'^https?:\/\/', url, re.IGNORECASE):
        url = 'http://' + url  # o 'https://', a tu elección

    # Intentar parsear la URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None

    # Reconstruir para normalizar
    return parsed.geturl()


def domain_exists(url: str) -> bool:
    """
    Verifica si el dominio de la URL responde con algún registro DNS.
    No es infalible (un DNS mal configurado puede dar falsos negativos),
    pero sirve como comprobación básica.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False

    # Aquí hacemos un pequeño truco con requests para ver si resuelve
    # (O podrías hacer socket.gethostbyname(hostname)).
    try:
        _ = requests.get(url, timeout=REQUEST_TIMEOUT)
        return True
    except:
        return False


def fetch_content(url: str) -> dict:
    """
    Devuelve un dict con 'error'=False y 'content' si todo va bien.
    Si no, 'error'=True y 'message'.
    Límite de 2MB a descargar.
    """
    try:
        # Stream=True nos deja controlar la descarga
        with requests.get(url, timeout=REQUEST_TIMEOUT, stream=True) as r:
            r.raise_for_status()

            # Limitar a MAX_DOWNLOAD_SIZE
            content_bytes = b''
            for chunk in r.iter_content(chunk_size=4096):
                content_bytes += chunk
                if len(content_bytes) > MAX_DOWNLOAD_SIZE:
                    return {
                        'error': True,
                        'message': f"Se superó el límite de {MAX_DOWNLOAD_SIZE} bytes."
                    }
            content = content_bytes.decode('utf-8', errors='replace')

        return {
            'error': False,
            'content': content
        }
    except Exception as e:
        return {
            'error': True,
            'message': str(e)
        }


def convert_relative_url(link: str, base_url: str) -> str:
    """
    Convierte un enlace relativo a uno absoluto, usando la URL base.
    Retorna None si no se puede parsear.
    """
    if not link:
        return None
    # Si ya es absoluta, la devolvemos tal cual
    parsed = urlparse(link)
    if parsed.scheme and parsed.netloc:
        return link

    return urljoin(base_url, link)


def process_domain(domain: str) -> dict:
    """
    Función principal que:
    1. Limpia y valida la URL de entrada,
    2. Comprueba si el dominio existe,
    3. Hace crawling hasta MAX_PAGES y MAX_DEPTH,
    4. Extrae emails y links de redes sociales,
    5. Devuelve un diccionario con los resultados.
    """
    url_inicial = clean_url(domain)
    if not url_inicial:
        return {
            'error': True,
            'message': 'URL inválida.'
        }

    if not domain_exists(url_inicial):
        return {
            'error': True,
            'message': 'El dominio no existe o no responde.'
        }

    visited = set()
    queue = deque()
    queue.append((url_inicial, 0))  # (URL, profundidad)
    emails = set()
    social_links = {key: set() for key in SOCIAL_REGEX.keys()}

    pages_crawled = 0

    while queue and pages_crawled < MAX_PAGES:
        current_url, depth = queue.popleft()
        if current_url in visited:
            continue
        visited.add(current_url)

        fetch_result = fetch_content(current_url)
        if fetch_result['error']:
            # Loguea el error y sigue con la siguiente URL
            # print(f"Error en {current_url}: {fetch_result['message']}")
            continue

        content = fetch_result['content']
        if not content:
            continue

        # Buscar correos
        email_matches = re.findall(EMAIL_REGEX, content, flags=re.IGNORECASE)
        for em in email_matches:
            em_lower = em.lower()
            # Verificar si contiene alguna palabra que lo excluye
            if any(word in em_lower for word in EXCLUDE_WORDS):
                continue
            emails.add(em_lower)

        # Buscar enlaces de redes sociales
        for platform, regex_pattern in SOCIAL_REGEX.items():
            match_list = re.findall(regex_pattern, content, flags=re.IGNORECASE)
            for match in match_list:
                # Asegurarnos de que sea un string (re.findall sin grupos de captura devuelve strings)
                if isinstance(match, str):
                    # Limpiar de posibles caracteres raros al final:
                    match_cleaned = match.rstrip('ª]')
                    social_links[platform].add(match_cleaned)

        # Extraer enlaces internos para continuar crawleando
        if depth < MAX_DEPTH:
            link_matches = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', content, flags=re.IGNORECASE)
            child_links_added = 0
            parsed_inicial = urlparse(url_inicial)

            for link in link_matches:
                absolute_link = convert_relative_url(link, current_url)
                if not absolute_link:
                    continue

                parsed_link = urlparse(absolute_link)
                # Agregamos solo si coincide el mismo dominio
                if parsed_link.netloc == parsed_inicial.netloc:
                    if absolute_link not in visited:
                        queue.append((absolute_link, depth + 1))
                        child_links_added += 1
                        if child_links_added >= MAX_CHILD_LINKS:
                            break

        pages_crawled += 1

    # Convertir sets a listas antes de retornar
    return {
        'error': False,
        'message': 'Crawling finalizado',
        'emails': sorted(list(emails)),
        'social_links': {k: sorted(list(v)) for k, v in social_links.items()}
    }


def main():
    """
    Si se llama directamente desde la terminal:
    - Espera 5 segundos para que el usuario introduzca un dominio.
    - Si no introduce nada, se usará 'centraldecomunicacion.es'.
    - Procesa el dominio y muestra el resultado por pantalla (JSON).
    """
    print("Introduce un dominio (e.g. www.midominio.com, http://otrodominio.es).")
    print("(Espera 5 segundos, si no introduces nada, se usará centraldecomunicacion.es)")

    # Usamos select para esperar lectura en sys.stdin con timeout de 5s
    domain_input = None
    rlist, _, _ = select.select([sys.stdin], [], [], 5)
    if rlist:
        domain_input = sys.stdin.readline().strip()

    domain = domain_input if domain_input else "centraldecomunicacion.es"

    data = process_domain(domain)

    # Mostrar resultado formateado
    print(json.dumps(data, indent=2, ensure_ascii=False))


# Si se ejecuta directamente con "python crawler.py", llamamos main().
# Si se importa desde otro lado, NO se llama main() automáticamente.
if __name__ == "__main__":
    main()
