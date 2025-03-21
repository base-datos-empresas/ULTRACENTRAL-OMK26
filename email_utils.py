#!/usr/bin/env python3
import dns.resolver
from email_validator import validate_email, EmailNotValidError
from colorama import Fore

def validate_email_address(email):
    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        return False, f"Formato inválido: {str(e)}"

    try:
        domain = email.split('@')[-1]
    except Exception:
        return False, "No se pudo extraer el dominio"

    try:
        answers = dns.resolver.resolve(domain, 'MX')
        if answers:
            return True, "Email válido (MX)"
    except Exception:
        pass

    try:
        answers = dns.resolver.resolve(domain, 'A')
        if answers:
            return True, "Email válido (A)"
    except Exception:
        return False, "No se encontraron registros DNS"

    return False, "Validación DNS fallida"

def filtrar_emails(emails, exclusiones):
    emails_validos = []
    for email in emails:
        if any(excl in email.lower() for excl in exclusiones):
            print(Fore.RED + f"🚫 EMAIL EXCLUIDO: {email}")
            continue

        is_valid, msg = validate_email_address(email)
        if not is_valid:
            print(Fore.RED + f"🚫 EMAIL INVÁLIDO ({msg}): {email}")
            continue

        emails_validos.append(email)
    return emails_validos
