"""
Injeção de dependência (composition root) do módulo de eleitores.

Mesmo padrão do `presentation/api/dependencies.py` (Módulo 1): monta cada
caso de uso a partir das implementações reais. Separado em arquivo
próprio para não deixar o `dependencies.py` do auth crescer sem limite
conforme novos módulos de negócio forem chegando.
"""

from typing import Annotated

from fastapi import Depends

from src.application.voters.create_voter import CreateVoterUseCase
from src.application.voters.delete_voter import DeleteVoterUseCase
from src.application.voters.get_voter import GetVoterUseCase
from src.application.voters.list_voters import ListVotersUseCase
from src.application.voters.update_voter import UpdateVoterUseCase
from src.infrastructure.database.repositories.voter_repository import SqlAlchemyVoterRepository
from src.presentation.api.dependencies import DbSession
from src.presentation.api.leaderships_dependencies import LeadershipRepositoryDep


def get_voter_repository(session: DbSession) -> SqlAlchemyVoterRepository:
    return SqlAlchemyVoterRepository(session)


VoterRepositoryDep = Annotated[SqlAlchemyVoterRepository, Depends(get_voter_repository)]


def get_create_voter_use_case(
    voter_repository: VoterRepositoryDep,
    leadership_repository: LeadershipRepositoryDep,
) -> CreateVoterUseCase:
    return CreateVoterUseCase(voter_repository, leadership_repository)


def get_get_voter_use_case(voter_repository: VoterRepositoryDep) -> GetVoterUseCase:
    return GetVoterUseCase(voter_repository)


def get_list_voters_use_case(voter_repository: VoterRepositoryDep) -> ListVotersUseCase:
    return ListVotersUseCase(voter_repository)


def get_update_voter_use_case(
    voter_repository: VoterRepositoryDep,
    leadership_repository: LeadershipRepositoryDep,
) -> UpdateVoterUseCase:
    return UpdateVoterUseCase(voter_repository, leadership_repository)


def get_delete_voter_use_case(voter_repository: VoterRepositoryDep) -> DeleteVoterUseCase:
    return DeleteVoterUseCase(voter_repository)
