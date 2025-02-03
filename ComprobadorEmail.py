#!/usr/bin/env python3
"""
ComprobadorEmail.py

Este módulo proporciona funciones para validar uno o varios correos electrónicos.
Si se recibe una cadena con múltiples correos separados por comas o punto y coma,
la función los separa, limpia y valida utilizando, preferentemente, la librería
email_validator para una verificación robusta. En caso de no estar disponible,
se utiliza una expresión regular como respaldo.
"""

import re

# Intentamos importar email_validator para una validación más robusta
try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False

if not EMAIL_VALIDATOR_AVAILABLE:
    # Expresión regular para validar el formato de un correo electrónico.
    # Esta expresión se usará solo si email_validator no está disponible.
    EMAIL_REGEX = re.compile(
        r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    )


def validar_email(email_str: str) -> list:
    """
    Valida uno o varios correos electrónicos.

    Separa la cadena de entrada usando comas o punto y coma como delimitadores,
    limpia los espacios en blanco y valida cada correo. Si la librería
    email_validator está disponible, se utiliza para normalizar el email; en
    caso contrario, se aplica una expresión regular.

    Args:
        email_str (str): Cadena que contiene uno o más correos separados por comas o punto y coma.

    Returns:
        list: Lista de correos electrónicos que cumplen con el formato válido.
    """
    if not email_str:
        return []

    # Separar la cadena por comas o punto y coma y eliminar entradas vacías
    posibles_emails = [e.strip() for e in re.split(r"[,;]+", email_str) if e.strip()]

    emails_validos = []
    for email in posibles_emails:
        if EMAIL_VALIDATOR_AVAILABLE:
            try:
                # La función validate_email devuelve un diccionario con la versión normalizada del email
                valid = validate_email(email)
                emails_validos.append(valid.email)
            except EmailNotValidError:
                # Si el email no es válido, se omite
                continue
        else:
            if EMAIL_REGEX.match(email):
                emails_validos.append(email)
    return emails_validos


def validar_email_externo(email_str: str) -> (list, list):
    """
    Función adicional para validar emails que retorna dos listas:
      - Lista de emails válidos.
      - Lista de emails inválidos.

    Esto resulta útil para análisis o reportes detallados.

    Args:
        email_str (str): Cadena que contiene uno o más correos separados por comas o punto y coma.

    Returns:
        tuple: (lista_validos, lista_invalidos)
    """
    if not email_str:
        return ([], [])
    posibles_emails = [e.strip() for e in re.split(r"[,;]+", email_str) if e.strip()]
    validos = []
    invalidos = []
    for email in posibles_emails:
        if EMAIL_VALIDATOR_AVAILABLE:
            try:
                valid = validate_email(email)
                validos.append(valid.email)
            except EmailNotValidError:
                invalidos.append(email)
        else:
            if EMAIL_REGEX.match(email):
                validos.append(email)
            else:
                invalidos.append(email)
    return validos, invalidos


if __name__ == "__main__":
    # Casos de prueba para verificar el funcionamiento de la validación
    pruebas = [
        "usuario@example.com",
        "no-email",
        "usuario@example.com, otro@ejemplo.com",
        "usuario@example, com, usuario2@example.com",
        " usuario@example.com ; otro@example.org;invalid-email "
    ]

    for prueba in pruebas:
        validos = validar_email(prueba)
        print(f"Entrada: {prueba}")
        print(f"Emails válidos: {validos}\n")
