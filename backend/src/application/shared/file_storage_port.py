"""
Porta (interface) de armazenamento de arquivo.

Abstrai o provedor (Cloudflare R2 na implementação concreta) atrás de
uma interface — mesmo padrão de `GeocodingService`/`WhatsAppSenderPort`.
"""

from abc import ABC, abstractmethod


class FileStoragePort(ABC):
    @abstractmethod
    async def upload(self, key: str, content: bytes, content_type: str) -> None:
        """Envia o arquivo pro armazenamento. `key` é o caminho completo dentro do bucket."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Remove o arquivo. NUNCA levanta exceção se o arquivo já não
        existir (idempotente) — quem chama não precisa checar existência
        antes, e uma segunda tentativa de remoção não deve quebrar nada.
        """

    @abstractmethod
    async def generate_download_url(self, key: str, expires_in_seconds: int = 900) -> str:
        """
        Gera uma URL temporária e assinada pra download direto do
        arquivo — o navegador baixa direto do R2, sem passar pelo nosso
        backend de novo (mais rápido, e não gasta banda do nosso
        servidor). Expira sozinha depois de `expires_in_seconds` (padrão
        15 minutos) — não é um link permanente público.
        """
