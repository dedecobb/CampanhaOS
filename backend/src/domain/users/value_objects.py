"""
Value Object: Email.

Por que um Value Object e não apenas `str`: e-mail tem uma regra de
validação de formato que se repetiria em vários lugares do sistema (cadastro
de usuário, convite de equipe, recuperação de senha...). Encapsulando aqui,
a regra existe em UM lugar só, e qualquer código que receba um `Email` já
sabe que ele é válido — não precisa validar de novo.

Value Objects são imutáveis (`frozen=True`) e comparados por valor, não por
identidade: dois `Email("a@a.com")` são iguais entre si.
"""

import re
from dataclasses import dataclass

from src.domain.shared.exceptions import InvalidEmailError

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_REGEX.match(normalized):
            raise InvalidEmailError(self.value)
        # dataclass frozen não permite atribuição normal, por isso object.__setattr__
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
