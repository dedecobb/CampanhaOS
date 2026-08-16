"""
Testes da validação de assinatura de webhook do Twilio.
"""

from src.infrastructure.whatsapp.twilio_signature import validate_twilio_signature


def test_validates_official_twilio_test_vector() -> None:
    """
    Vetor de teste OFICIAL da documentação do Twilio
    (https://www.twilio.com/docs/usage/webhooks/webhooks-security) —
    prova que a implementação do algoritmo está correta, não só "parece
    certa".
    """
    auth_token = "12345"
    url = "https://mycompany.com/myapp.php?foo=1&bar=2"
    params = {
        "CallSid": "CA1234567890ABCDE",
        "Caller": "+14158675309",
        "Digits": "1234",
        "From": "+14158675309",
        "To": "+18005551212",
    }
    expected_signature = "RSOYDt4T1cUTdK1PDd93/VVr8B8="

    assert validate_twilio_signature(auth_token, url, params, expected_signature) is True


def test_rejects_forged_signature() -> None:
    result = validate_twilio_signature(
        "12345", "https://mycompany.com/myapp.php", {"Body": "oi"}, "assinatura_forjada="
    )
    assert result is False


def test_rejects_tampered_payload_with_original_signature() -> None:
    """Payload alterado depois de assinado deve ser rejeitado, mesmo reusando a assinatura original."""
    auth_token = "12345"
    url = "https://mycompany.com/myapp.php?foo=1&bar=2"
    original_params = {
        "CallSid": "CA1234567890ABCDE",
        "Caller": "+14158675309",
        "Digits": "1234",
        "From": "+14158675309",
        "To": "+18005551212",
    }
    original_signature = "RSOYDt4T1cUTdK1PDd93/VVr8B8="

    tampered_params = dict(original_params)
    tampered_params["Digits"] = "9999"

    assert validate_twilio_signature(auth_token, url, tampered_params, original_signature) is False
