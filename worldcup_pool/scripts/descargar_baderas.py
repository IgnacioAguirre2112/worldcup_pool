import os
import time
import requests

# Carpeta destino
OUTPUT_DIR = "assets/flags"

# Países del Mundial 2026 según tu imagen
FLAGS = {
    "mexico": "mx",
    "sudafrica": "za",
    "corea_sur": "kr",
    "chequia": "cz",
    "canada": "ca",
    "bosnia": "ba",
    "qatar": "qa",
    "suiza": "ch",
    "brasil": "br",
    "marruecos": "ma",
    "haiti": "ht",
    "escocia": "gb-sct",
    "estados_unidos": "us",
    "paraguay": "py",
    "australia": "au",
    "turquia": "tr",
    "alemania": "de",
    "curazao": "cw",
    "costa_marfil": "ci",
    "ecuador": "ec",
    "paises_bajos": "nl",
    "japon": "jp",
    "suecia": "se",
    "tunez": "tn",
    "belgica": "be",
    "egipto": "eg",
    "iran": "ir",
    "nueva_zelanda": "nz",
    "espana": "es",
    "cabo_verde": "cv",
    "arabia_saudita": "sa",
    "uruguay": "uy",
    "francia": "fr",
    "senegal": "sn",
    "irak": "iq",
    "noruega": "no",
    "argentina": "ar",
    "argelia": "dz",
    "austria": "at",
    "jordania": "jo",
    "portugal": "pt",
    "rd_congo": "cd",
    "uzbekistan": "uz",
    "colombia": "co",
    "inglaterra": "gb-eng",
    "croacia": "hr",
    "ghana": "gh",
    "panama": "pa",
}

def descargar_bandera(nombre, codigo):
    url = f"https://flagcdn.com/w320/{codigo}.png"

    try:
        response = requests.get(url, timeout=20)

        if response.status_code == 200:
            ruta = os.path.join(OUTPUT_DIR, f"{nombre}.png")

            with open(ruta, "wb") as f:
                f.write(response.content)

            print(f"✓ Descargada: {nombre}")

        else:
            print(f"✗ Error {response.status_code}: {nombre}")

    except Exception as e:
        print(f"✗ Error descargando {nombre}: {e}")

def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 50)
    print("DESCARGA DE BANDERAS MUNDIAL 2026")
    print("=" * 50)

    for nombre, codigo in FLAGS.items():
        descargar_bandera(nombre, codigo)
        time.sleep(0.2)

    print("\nProceso finalizado.")
    print(f"Banderas guardadas en: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()