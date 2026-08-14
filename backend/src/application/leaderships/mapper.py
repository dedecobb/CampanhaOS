from src.application.leaderships.dto import LeadershipOutput
from src.domain.leaderships.entities import Leadership


def leadership_to_output(leadership: Leadership) -> LeadershipOutput:
    return LeadershipOutput(
        id=leadership.id,
        created_by_user_id=leadership.created_by_user_id,
        name=leadership.name,
        region=leadership.region,
        estimated_votes=leadership.estimated_votes,
        influence_level=leadership.influence_level,
        team_size=leadership.team_size,
        notes=leadership.notes,
        created_at=leadership.created_at,
        updated_at=leadership.updated_at,
    )
