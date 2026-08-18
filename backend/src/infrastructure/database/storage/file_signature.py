"""
Detecção de tipo de arquivo pela ASSINATURA REAL dos bytes (os primeiros
bytes de todo arquivo desses formatos seguem um padrão fixo, conhecido
como "magic bytes") — nunca confiar na extensão do nome do arquivo nem
no `Content-Type` que o navegador declara no upload, os dois são fáceis
de forjar (renomear um `.exe` pra `.pdf` não muda o conteúdo real).
"""

_JPEG_SIGNATURE = b"\xff\xd8\xff"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PDF_SIGNATURE = b"%PDF"


def detect_content_type(file_bytes: bytes) -> str | None:
    """
    Retorna o content-type REAL detectado pela assinatura dos bytes, ou
    `None` se não bater com nenhum dos 3 formatos aceitos (JPEG, PNG,
    PDF) — nesse caso, quem chama deve rejeitar o upload, independente
    do que o nome do arquivo ou o header da requisição alegam ser.
    """
    if file_bytes.startswith(_JPEG_SIGNATURE):
        return "image/jpeg"
    if file_bytes.startswith(_PNG_SIGNATURE):
        return "image/png"
    if file_bytes.startswith(_PDF_SIGNATURE):
        return "application/pdf"
    return None
