"""
Validação de assinatura de webhooks do Twilio.

https://www.twilio.com/docs/usage/webhooks/webhooks-security

CRÍTICO: o endpoint de webhook é público (a Meta/Twilio precisa
conseguir chamá-lo sem nenhuma autenticação nossa) — sem essa validação,
qualquer pessoa na internet poderia mandar uma requisição forjada pro
nosso endpoint fingindo ser uma mensagem de WhatsApp de verdade, criando
opt-ins falsos ou disparando descadastros indevidos.
"""

import base64
import hashlib
import hmac


def validate_twilio_signature(
    auth_token: str,
    full_url: str,
    post_params: dict[str, str],
    signature_header: str,
) -> bool:
    """
    Algoritmo oficial do Twilio: concatena a URL completa (exatamente
    como configurada no painel do Twilio, incluindo query string se
    houver) com cada par chave+valor do corpo do POST, EM ORDEM
    ALFABÉTICA da chave, sem separador nenhum entre eles. Assina esse
    texto com HMAC-SHA1 usando o Auth Token como chave, codifica em
    base64, e compara com o header `X-Twilio-Signature`.
    """
    data = full_url
    for key in sorted(post_params.keys()):
        data += key + post_params[key]

    computed_signature = base64.b64encode(
        hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")

    # hmac.compare_digest evita "timing attack" — comparar string com
    # `==` normal vazaria informação sobre em qual posição a comparação
    # falhou, através do tempo que a comparação leva para retornar.
    return hmac.compare_digest(computed_signature, signature_header)
