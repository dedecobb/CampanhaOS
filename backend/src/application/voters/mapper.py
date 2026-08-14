"""
Mapeamento entre a entidade de domínio `Voter` e o DTO `VoterOutput`.

Extraído como função própria porque é reaproveitado por praticamente todo
caso de uso deste módulo (create, get, update, list) — evita repetir a
mesma construção de objeto em 4 arquivos diferentes.
"""

from src.application.voters.dto import VoterOutput
from src.domain.voters.entities import Voter


def voter_to_output(voter: Voter) -> VoterOutput:
    return VoterOutput(
        id=voter.id,
        created_by_user_id=voter.created_by_user_id,
        name=voter.name,
        phone=voter.phone,
        address=voter.address,
        latitude=voter.latitude,
        longitude=voter.longitude,
        tags=voter.tags,
        custom_fields=voter.custom_fields,
        notes=voter.notes,
        legal_basis=voter.legal_basis,
        created_at=voter.created_at,
        updated_at=voter.updated_at,
        leadership_id=voter.leadership_id,
    )
