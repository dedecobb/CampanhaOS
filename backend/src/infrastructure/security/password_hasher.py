"""
Implementação real de PasswordHasher usando bcrypt (via passlib).

bcrypt é a escolha padrão de mercado para hash de senha porque é
propositalmente lento (fator de custo configurável) — isso é uma feature,
não um bug: dificulta ataques de força bruta mesmo se o hash vazar.
"""

from passlib.context import CryptContext

from src.application.auth.ports import PasswordHasher

# `deprecated="auto"`: se um dia trocarmos/adicionarmos outro algoritmo de
# hash na lista `schemes`, o passlib identifica automaticamente hashes
# antigos como "precisam ser re-hasheados no próximo login bem-sucedido" —
# um mecanismo de migração de algoritmo pronto, sem precisarmos escrever
# essa lógica manualmente no futuro.
_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, plain_password: str) -> str:
        return _context.hash(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return _context.verify(plain_password, password_hash)
