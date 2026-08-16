"""
Entidade de domínio: WhatsAppContact.

Esta é a peça CENTRAL de compliance do módulo (ver ADR de decisão de
negócio, documento fonte da verdade): a Resolução TSE 23.610/2019 (e
atualizações pra 2026) proíbe disparo em massa e exige que o contato
tenha "adicionado o número do candidato" por conta própria — ou seja, o
opt-in precisa vir do ELEITOR iniciando o contato, nunca da campanha.

Por isso `opt_in_source` é sempre "contato_iniciou_conversa" nesta
versão — não existe (de propósito) nenhum caminho no código pra criar um
WhatsAppContact a partir de uma lista importada ou comprada.
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.shared.exceptions import DomainError

# Formato E.164 simplificado: + seguido de 8 a 15 dígitos. Não valida
# se o número é um WhatsApp válido de verdade (isso só a própria Meta
# sabe) — só o formato básico.
_PHONE_PATTERN = re.compile(r"^\+\d{8,15}$")


class InvalidPhoneNumberError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(
            f"Número de telefone '{value}' inválido — formato esperado: "
            f"'+' seguido do código do país e DDD (ex: +5521999998888)"
        )


@dataclass
class WhatsAppContact:
    id: UUID
    tenant_id: UUID
    phone_number: str
    voter_id: UUID | None
    opted_in_at: datetime
    opt_in_source: str
    opted_out_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        tenant_id: UUID,
        phone_number: str,
        opt_in_source: str = "contato_iniciou_conversa",
        voter_id: UUID | None = None,
    ) -> "WhatsAppContact":
        WhatsAppContact._validate_phone_number(phone_number)

        now = datetime.now(UTC)
        return WhatsAppContact(
            id=uuid4(),
            tenant_id=tenant_id,
            phone_number=phone_number,
            voter_id=voter_id,
            opted_in_at=now,
            opt_in_source=opt_in_source,
            opted_out_at=None,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _validate_phone_number(phone_number: str) -> None:
        if not _PHONE_PATTERN.match(phone_number):
            raise InvalidPhoneNumberError(phone_number)

    @property
    def is_opted_in(self) -> bool:
        return self.opted_out_at is None

    def opt_out(self) -> None:
        """Contato pediu descadastro — RN explícita do TSE: mensagem precisa oferecer essa opção."""
        self.opted_out_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def opt_in_again(self) -> None:
        """Contato que tinha saído voltou a mandar mensagem — reativa o consentimento."""
        self.opted_out_at = None
        self.opted_in_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def link_to_voter(self, voter_id: UUID) -> None:
        """Associa este contato a um Voter já cadastrado (match por telefone)."""
        self.voter_id = voter_id
        self.updated_at = datetime.now(UTC)
