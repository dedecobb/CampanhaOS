from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class GetDashboardStatsInput:
    tenant_id: UUID


@dataclass(frozen=True)
class RegistrationGrowthPoint:
    day: date
    count: int


@dataclass(frozen=True)
class LeadershipBreakdownPoint:
    leadership_name: str
    count: int


@dataclass(frozen=True)
class DashboardStatsOutput:
    total_voters: int
    voter_goal: int | None
    gender_breakdown: dict[str, int] = field(default_factory=dict)
    age_breakdown: dict[str, int] = field(default_factory=dict)
    registration_growth: list[RegistrationGrowthPoint] = field(default_factory=list)
    self_registered_count: int = 0
    staff_registered_count: int = 0
    leadership_breakdown: list[LeadershipBreakdownPoint] = field(default_factory=list)


@dataclass(frozen=True)
class SetVoterGoalInput:
    tenant_id: UUID
    goal: int


@dataclass(frozen=True)
class ClearVoterGoalInput:
    tenant_id: UUID
