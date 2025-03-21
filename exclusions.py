#!/usr/bin/env python3
import os
from colorama import Fore
from configuracion import EXCLUSIONES_FOLDER

def cargar_exclusiones():
    exclusiones = set()
    if not os.path.exists(EXCLUSIONES_FOLDER) or not os.listdir(EXCLUSIONES_FOLDER):
        print(Fore.RED + f"🚨 La carpeta '{EXCLUSIONES_FOLDER}' está vacía. No se aplicarán exclusiones.")
        return exclusiones

    for file in os.listdir(EXCLUSIONES_FOLDER):
        file_path = os.path.join(EXCLUSIONES_FOLDER, file)
        if os.path.isfile(file_path) and file.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    palabra = line.strip().lower()
                    if palabra:
                        exclusiones.add(palabra)
    print(Fore.GREEN + f"✅ Exclusiones cargadas: {len(exclusiones)} palabras clave.")
    return exclusiones
