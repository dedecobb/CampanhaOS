from src.application.events.dto import EventOutput
from src.domain.events.entities import Event


def event_to_output(event: Event) -> EventOutput:
    return EventOutput(
        id=event.id,
        created_by_user_id=event.created_by_user_id,
        responsible_user_id=event.responsible_user_id,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        status=event.status,
        location=event.location,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        voter_id=event.voter_id,
        leadership_id=event.leadership_id,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
