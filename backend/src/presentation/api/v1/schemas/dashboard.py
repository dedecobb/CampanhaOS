from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class RegistrationGrowthPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: date
    count: int


class DashboardStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_voters: int
    voter_goal: int | None
    gender_breakdown: dict[str, int]
    age_breakdown: dict[str, int]
    registration_growth: list[RegistrationGrowthPointResponse]
    self_registered_count: int
    staff_registered_count: int


class SetVoterGoalRequest(BaseModel):
    goal: int = Field(..., gt=0)
