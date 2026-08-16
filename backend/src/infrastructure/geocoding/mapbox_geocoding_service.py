"""
Implementação concreta de GeocodingService usando a API de Geocoding do
Mapbox (https://docs.mapbox.com/api/search/geocoding/).
"""

from urllib.parse import quote

import httpx

from src.application.geocoding.ports import Coordinates, GeocodingService

_MAPBOX_GEOCODING_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json"


class MapboxGeocodingService(GeocodingService):
    def __init__(self, access_token: str, timeout_seconds: float = 5.0) -> None:
        self._access_token = access_token
        self._timeout_seconds = timeout_seconds

    async def geocode(self, address: str) -> Coordinates | None:
        if not address or not address.strip():
            return None

        url = _MAPBOX_GEOCODING_URL.format(encoded_address=quote(address.strip()))
        params = {
            "access_token": self._access_token,
            "limit": 1,
            # Restringe ao Brasil — evita resultado geocodificado num
            # país errado para um endereço ambíguo/incompleto.
            "country": "BR",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            # Rede fora, timeout, resposta não-JSON, etc. — geocodificação
            # é melhoria, não requisito (ver contrato da porta). Nunca
            # propaga a exceção para quem chamou.
            return None

        features = data.get("features", [])
        if not features:
            return None

        # Mapbox retorna [longitude, latitude] (ordem GeoJSON), invertido
        # em relação à ordem "natural" (latitude, longitude) — erro fácil
        # de cometer se copiar sem prestar atenção.
        longitude, latitude = features[0]["center"]
        return Coordinates(latitude=latitude, longitude=longitude)
