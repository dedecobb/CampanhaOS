"""
Porta (interface) de envio de mensagem WhatsApp.

Abstrai o provedor (BSP — Twilio na nossa implementação, mas poderia ser
Gupshup/360dialog/etc.) atrás de uma interface, mesmo padrão de
`GeocodingService` (Módulo de Mapa) — trocar de provedor no futuro
significa só escrever uma nova implementação em `infrastructure/`.
"""

from abc import ABC, abstractmethod


class WhatsAppSenderPort(ABC):
    @abstractmethod
    async def send_template_message(
        self,
        to_phone_number: str,
        template_sid: str,
        template_variables: dict[str, str] | None = None,
    ) -> bool:
        """
        Envia mensagem usando um TEMPLATE PRÉ-APROVADO — nunca texto
        livre. Isso não é só uma limitação técnica do WhatsApp Business
        (mensagens de negócio iniciadas fora da janela de 24h de
        atendimento exigem template aprovado pela Meta), é também parte
        do compliance deste módulo: um template aprovado previamente
        já passou pela checagem de conteúdo da Meta, reduzindo o risco
        de propaganda irregular passar despercebida.

        `template_sid` é o identificador do template no BSP (no Twilio,
        um "Content SID", formato `HXxxxxxxxx...`) — não o nome livre do
        template, que só existe no painel de aprovação da Meta/BSP.

        Retorna `True`/`False` conforme sucesso — nunca levanta exceção
        (mesmo contrato de "falha não deve quebrar o restante do fluxo"
        já usado em GeocodingService).
        """
