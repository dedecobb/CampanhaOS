"""
Implementação concreta de GeocodingService usando a API de Geocoding v6
do Mapbox, com ENTRADA ESTRUTURADA
(https://docs.mapbox.com/api/search/geocoding/#forward-geocoding-with-structured-input).

Por que v6 estruturada, e não v5 com uma string única concatenada (nossa
primeira tentativa): passar "endereço, cidade, estado, CEP, Brasil" como
um texto livre único deixa o Mapbox tendo que ADIVINHAR qual pedaço da
string é rua, qual é cidade, qual é estado — e essa adivinhação erra,
inclusive colocando o resultado no estado errado (foi exatamente o que
aconteceu na prática, ver documento fonte da verdade). Com entrada
estruturada, cada parte vai num parâmetro próprio (`address_line1`,
`place`, `region`, `postcode`) — sem adivinhação nenhuma.
"""

import httpx

from src.application.geocoding.ports import Coordinates, GeocodingService

_MAPBOX_GEOCODING_V6_URL = "https://api.mapbox.com/search/geocode/v6/forward"


class MapboxGeocodingService(GeocodingService):
    def __init__(self, access_token: str, timeout_seconds: float = 5.0) -> None:
        self._access_token = access_token
        self._timeout_seconds = timeout_seconds

    async def geocode(
        self,
        address_line: str,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
    ) -> Coordinates | None:
        if not address_line or not address_line.strip():
            return None

        params: dict[str, str | int] = {
            "access_token": self._access_token,
            "address_line1": address_line.strip(),
            "country": "br",
            "limit": 1,
        }
        # Só inclui os parâmetros estruturados que de fato temos — o
        # Mapbox lida bem com parâmetros ausentes, não precisa mandar
        # string vazia.
        if city:
            params["place"] = city.strip()
        if state:
            params["region"] = state.strip()
        if postal_code:
            params["postcode"] = postal_code.strip()

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(_MAPBOX_GEOCODING_V6_URL, params=params)
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

        # v6 retorna GeoJSON padrão: geometry.coordinates = [longitude, latitude]
        # (mesma ordem "invertida" da v5, mas em outro caminho do JSON).
        longitude, latitude = features[0]["geometry"]["coordinates"]
        return Coordinates(latitude=latitude, longitude=longitude)
