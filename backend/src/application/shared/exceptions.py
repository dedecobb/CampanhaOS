"""
Classe-base de exceções de caso de uso, compartilhada por todos os
módulos de aplicação (auth, voters, e os futuros).

Movida aqui a partir de application/auth/exceptions.py no Módulo 2 —
antes só existia um módulo de aplicação, então não fazia diferença onde
essa classe morava; com o segundo módulo, faz sentido ela ser compartilhada
em vez de "pertencer" ao auth.
"""


class ApplicationError(Exception):
    """Classe base para erros de caso de uso, em qualquer módulo."""
