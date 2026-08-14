"""
Script de bootstrap: cria um PlatformAdmin (super-admin da plataforma).

Não existe endpoint HTTP público para isso, de propósito — um endpoint de
"criar super-admin" acessível pela internet seria uma porta de entrada
para comprometer o sistema inteiro (todos os tenants). Este script só
pode ser executado com acesso direto ao container/banco, o que já exige
um nível de acesso bem mais restrito.

Uso:
    docker compose exec backend python -m scripts.create_platform_admin \
        --name "Seu Nome" --email "voce@campanhaos.com" --password "senha_forte_123"
"""

import argparse
import asyncio
import sys

from src.domain.admin.entities import PlatformAdmin
from src.domain.users.value_objects import Email
from src.infrastructure.database.repositories.platform_admin_repository import SqlAlchemyPlatformAdminRepository
from src.infrastructure.database.session import AsyncSessionFactory
from src.infrastructure.security.password_hasher import BcryptPasswordHasher


async def create_platform_admin(name: str, email: str, password: str) -> None:
    if len(password) < 8:
        print("Erro: a senha precisa ter ao menos 8 caracteres.", file=sys.stderr)
        sys.exit(1)

    async with AsyncSessionFactory() as session:
        repository = SqlAlchemyPlatformAdminRepository(session)

        existing = await repository.find_by_email(Email(email))
        if existing is not None:
            print(f"Erro: já existe um administrador com o e-mail '{email}'.", file=sys.stderr)
            sys.exit(1)

        hasher = BcryptPasswordHasher()
        admin = PlatformAdmin.create(name=name, email=Email(email), password_hash=hasher.hash(password))
        await repository.save(admin)
        await session.commit()

        print(f"Super-admin criado com sucesso: {admin.name} <{admin.email}> (id={admin.id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um super-admin da plataforma CampanhaOS.")
    parser.add_argument("--name", required=True, help="Nome do administrador")
    parser.add_argument("--email", required=True, help="E-mail (único na plataforma)")
    parser.add_argument("--password", required=True, help="Senha (mínimo 8 caracteres)")
    args = parser.parse_args()

    asyncio.run(create_platform_admin(args.name, args.email, args.password))


if __name__ == "__main__":
    main()
