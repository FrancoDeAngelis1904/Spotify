"""
spotify_genre_autocollector.py

Versión pensada para correr SOLA, sin login interactivo (GitHub Actions
o cualquier servidor). Usa un refresh_token ya generado con
get_refresh_token.py para conseguir un access_token nuevo en cada corrida.
"""

import base64
import json
import os
from datetime import datetime, timedelta

import requests
import spotipy

# ---------------------------------------------------------------------------
# CONFIGURACIÓN — lo único que tenés que tocar
# ---------------------------------------------------------------------------

GENERO_A_PLAYLIST = {
    "techno": "TU_PLAYLIST_ID_TECHNO",
    "uk garage": "TU_PLAYLIST_ID_UKGARAGE",
    "electro pop": "TU_PLAYLIST_ID_ELECTROPOP",
    # agregá las que necesites
}

DIAS_PARA_CONSIDERAR_NUEVO = 14
MERCADO = "AR"
RESULTADOS_POR_PAGINA = 10   # máximo permitido en Dev Mode desde feb 2026
PAGINAS_POR_GENERO = 5       # 5 páginas x 10 = hasta 50 resultados por género

ARCHIVO_PROCESADOS = "procesados.json"

# ---------------------------------------------------------------------------
# AUTENTICACIÓN SIN NAVEGADOR (usa el refresh token guardado como secret)
# ---------------------------------------------------------------------------

def obtener_access_token():
    auth_header = base64.b64encode(
        f"{os.environ['SPOTIFY_CLIENT_ID']}:{os.environ['SPOTIFY_CLIENT_SECRET']}".encode()
    ).decode()

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth_header}"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def autenticar():
    return spotipy.Spotify(auth=obtener_access_token())


# ---------------------------------------------------------------------------
# PERSISTENCIA: qué temas ya agregamos, para no repetir
# ---------------------------------------------------------------------------

def cargar_procesados():
    if os.path.exists(ARCHIVO_PROCESADOS):
        with open(ARCHIVO_PROCESADOS, "r") as f:
            return set(json.load(f))
    return set()


def guardar_procesados(procesados):
    with open(ARCHIVO_PROCESADOS, "w") as f:
        json.dump(list(procesados), f)


# ---------------------------------------------------------------------------
# LÓGICA PRINCIPAL
# ---------------------------------------------------------------------------

def es_nuevo(track, dias=DIAS_PARA_CONSIDERAR_NUEVO):
    fecha_str = track["album"]["release_date"]
    precision = track["album"]["release_date_precision"]

    if precision == "day":
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    elif precision == "month":
        fecha = datetime.strptime(fecha_str, "%Y-%m")
    else:
        fecha = datetime.strptime(fecha_str, "%Y")

    return datetime.now() - fecha <= timedelta(days=dias)


def buscar_nuevos_por_genero(sp, genero, procesados):
    query = f'genre:"{genero}"'
    nuevos = []

    for pagina in range(PAGINAS_POR_GENERO):
        offset = pagina * RESULTADOS_POR_PAGINA
        resultados = sp.search(
            q=query, type="track", market=MERCADO,
            limit=RESULTADOS_POR_PAGINA, offset=offset,
        )
        items = resultados["tracks"]["items"]
        if not items:
            break

        for track in items:
            if track["id"] in procesados:
                continue
            if es_nuevo(track):
                nuevos.append(track)

    return nuevos


def main():
    sp = autenticar()
    procesados = cargar_procesados()

    for genero, playlist_id in GENERO_A_PLAYLIST.items():
        nuevos = buscar_nuevos_por_genero(sp, genero, procesados)

        if nuevos:
            ids = [t["id"] for t in nuevos]
            sp.playlist_add_items(playlist_id, ids)
            print(f"[{genero}] agregados {len(ids)} temas nuevos:")
            for t in nuevos:
                print(f"   - {t['artists'][0]['name']} - {t['name']}")
            procesados.update(ids)
        else:
            print(f"[{genero}] sin novedades")

    guardar_procesados(procesados)


if __name__ == "__main__":
    main()
