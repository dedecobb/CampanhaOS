"""
Implementação concreta de WhatsAppSenderPort usando o Twilio como BSP
(Business Solution Provider) autorizado pela Meta.

https://www.twilio.com/docs/whatsapp/api
"""

import json

import httpx

from src.application.whatsapp.ports import WhatsAppSenderPort

_TWILIO_MESSAGES_URL = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"


class TwilioWhatsAppSender(WhatsAppSenderPort):
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._account_sid = account_sid
        self._auth_token = auth_token
        # `from_number` já deve vir no formato "whatsapp:+14155238886"
        # (o próprio painel do Twilio mostra o número já formatado assim).
        self._from_number = from_number
        self._timeout_seconds = timeout_seconds

    async def send_template_message(
        self,
        to_phone_number: str,
        template_sid: str,
        template_variables: dict[str, str] | None = None,
    ) -> bool:
        url = _TWILIO_MESSAGES_URL.format(account_sid=self._account_sid)

        data = {
            "From": self._from_number,
            "To": f"whatsapp:{to_phone_number}",
            "ContentSid": template_sid,
        }
        if template_variables:
            # Twilio espera as variáveis do template como uma string
            # JSON, não um objeto de verdade no corpo do form.
            data["ContentVariables"] = json.dumps(template_variables)

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self._account_sid, self._auth_token),
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError:
            # Falha de envio não deve derrubar o restante do fluxo de
            # quem chamou — mesmo contrato de GeocodingService.
            return False
