"""
get_refresh_token.py

Corré esto UNA SOLA VEZ, en tu computadora (no en GitHub Actions),
para obtener el refresh_token que después vas a guardar como Secret
en tu repo de GitHub.

Requiere:
    pip install spotipy

Antes de correrlo:
    export SPOTIFY_CLIENT_ID="tu_id"
    export SPOTIFY_CLIENT_SECRET="tu_secret"
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPE = "playlist-modify-public playlist-modify-private"

auth_manager = SpotifyOAuth(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    redirect_uri="http://127.0.0.1:8888/callback",
    scope=SCOPE,
)

sp = spotipy.Spotify(auth_manager=auth_manager)
sp.current_user()  # esto abre el navegador y fuerza el login una vez

token_info = auth_manager.cache_handler.get_cached_token()
print("\n¡Listo! Este es tu refresh token. Guardalo como Secret SPOTIFY_REFRESH_TOKEN en GitHub:\n")
print(token_info["refresh_token"])
