"""
Injeção de dependência (composition root) do módulo de lideranças.
"""

from typing import Annotated

from fastapi import Depends

from src.application.leaderships.create_leadership import CreateLeadershipUseCase
from src.application.leaderships.delete_leadership import DeleteLeadershipUseCase
from src.application.leaderships.get_leadership import GetLeadershipUseCase
from src.application.leaderships.get_voter_counts import GetLeadershipVoterCountsUseCase
from src.application.leaderships.list_leaderships import ListLeadershipsUseCase
from src.application.leaderships.update_leadership import UpdateLeadershipUseCase
from src.infrastructure.database.repositories.leadership_repository import SqlAlchemyLeadershipRepository
from src.infrastructure.database.repositories.voter_repository import SqlAlchemyVoterRepository
from src.presentation.api.dependencies import DbSession


def get_leadership_repository(session: DbSession) -> SqlAlchemyLeadershipRepository:
    return SqlAlchemyLeadershipRepository(session)


def get_voter_repository_for_leadership_counts(session: DbSession) -> SqlAlchemyVoterRepository:
    # Nome verboso de propósito — deixa claro, só de ler a assinatura, que
    # é o MESMO SqlAlchemyVoterRepository de sempre, só reaproveitado
    # aqui porque a contagem de eleitores por liderança mora no
    # VoterRepository (é uma pergunta sobre eleitores, agrupada por
    # liderança), não no LeadershipRepository.
    return SqlAlchemyVoterRepository(session)


LeadershipRepositoryDep = Annotated[SqlAlchemyLeadershipRepository, Depends(get_leadership_repository)]
VoterRepositoryForLeadershipCountsDep = Annotated[
    SqlAlchemyVoterRepository, Depends(get_voter_repository_for_leadership_counts)
]


def get_create_leadership_use_case(leadership_repository: LeadershipRepositoryDep) -> CreateLeadershipUseCase:
    return CreateLeadershipUseCase(leadership_repository)


def get_get_leadership_use_case(leadership_repository: LeadershipRepositoryDep) -> GetLeadershipUseCase:
    return GetLeadershipUseCase(leadership_repository)


def get_list_leaderships_use_case(leadership_repository: LeadershipRepositoryDep) -> ListLeadershipsUseCase:
    return ListLeadershipsUseCase(leadership_repository)


def get_update_leadership_use_case(leadership_repository: LeadershipRepositoryDep) -> UpdateLeadershipUseCase:
    return UpdateLeadershipUseCase(leadership_repository)


def get_delete_leadership_use_case(leadership_repository: LeadershipRepositoryDep) -> DeleteLeadershipUseCase:
    return DeleteLeadershipUseCase(leadership_repository)


def get_leadership_voter_counts_use_case(
    voter_repository: VoterRepositoryForLeadershipCountsDep,
) -> GetLeadershipVoterCountsUseCase:
    return GetLeadershipVoterCountsUseCase(voter_repository)
