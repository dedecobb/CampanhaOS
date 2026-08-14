"""
Injeção de dependência (composition root) do módulo de eventos (Agenda).

Reaproveita `get_user_repository` (auth), `get_voter_repository` (voters)
e `get_leadership_repository` (leaderships) já existentes — não
redefinimos nada disso aqui, só compomos.
"""

from typing import Annotated

from fastapi import Depends

from src.application.events.create_event import CreateEventUseCase
from src.application.events.delete_event import DeleteEventUseCase
from src.application.events.get_event import GetEventUseCase
from src.application.events.list_events import ListEventsUseCase
from src.application.events.update_event import UpdateEventUseCase
from src.infrastructure.database.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.database.repositories.user_repository import SqlAlchemyUserRepository
from src.presentation.api.dependencies import DbSession, get_user_repository
from src.presentation.api.leaderships_dependencies import LeadershipRepositoryDep
from src.presentation.api.voters_dependencies import VoterRepositoryDep


def get_event_repository(session: DbSession) -> SqlAlchemyEventRepository:
    return SqlAlchemyEventRepository(session)


EventRepositoryDep = Annotated[SqlAlchemyEventRepository, Depends(get_event_repository)]
UserRepositoryDep = Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)]


def get_create_event_use_case(
    event_repository: EventRepositoryDep,
    user_repository: UserRepositoryDep,
    voter_repository: VoterRepositoryDep,
    leadership_repository: LeadershipRepositoryDep,
) -> CreateEventUseCase:
    return CreateEventUseCase(event_repository, user_repository, voter_repository, leadership_repository)


def get_get_event_use_case(event_repository: EventRepositoryDep) -> GetEventUseCase:
    return GetEventUseCase(event_repository)


def get_list_events_use_case(event_repository: EventRepositoryDep) -> ListEventsUseCase:
    return ListEventsUseCase(event_repository)


def get_update_event_use_case(
    event_repository: EventRepositoryDep,
    user_repository: UserRepositoryDep,
    voter_repository: VoterRepositoryDep,
    leadership_repository: LeadershipRepositoryDep,
) -> UpdateEventUseCase:
    return UpdateEventUseCase(event_repository, user_repository, voter_repository, leadership_repository)


def get_delete_event_use_case(event_repository: EventRepositoryDep) -> DeleteEventUseCase:
    return DeleteEventUseCase(event_repository)
