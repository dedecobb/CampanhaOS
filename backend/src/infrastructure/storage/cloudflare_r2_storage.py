"""
Implementação concreta de FileStoragePort usando Cloudflare R2.

R2 é compatível com a API do S3 — por isso usamos `boto3` (SDK oficial da
AWS) apontado pro endpoint do R2, em vez de escrever um cliente HTTP do
zero. `boto3` é SÍNCRONO (não tem suporte async nativo) — por isso toda
chamada aqui passa por `asyncio.to_thread`, que roda a chamada bloqueante
numa thread separada, sem travar o loop de eventos do FastAPI.
"""

import asyncio

import boto3
from botocore.client import Config

from src.application.shared.file_storage_port import FileStoragePort


class CloudflareR2Storage(FileStoragePort):
    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ) -> None:
        self._bucket_name = bucket_name
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",  # R2 não usa regiões AWS de verdade — "auto" é o valor esperado
        )

    async def upload(self, key: str, content: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    async def delete(self, key: str) -> None:
        # delete_object do S3/R2 já é naturalmente idempotente — não dá
        # erro se a chave não existir, então não precisa de try/except
        # aqui pra cumprir o contrato da porta (ver docstring).
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket_name, Key=key)

    async def generate_download_url(self, key: str, expires_in_seconds: int = 900) -> str:
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket_name, "Key": key},
            ExpiresIn=expires_in_seconds,
        )
