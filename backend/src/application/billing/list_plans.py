from src.application.billing.dto import ListPlansInput, PlanOutput
from src.application.billing.mapper import plan_to_output
from src.domain.billing.repository import PlanRepository


class ListPlansUseCase:
    def __init__(self, plan_repository: PlanRepository) -> None:
        self._plan_repository = plan_repository

    async def execute(self, input_data: ListPlansInput) -> list[PlanOutput]:
        plans = await self._plan_repository.list_all(only_active=input_data.only_active)
        return [plan_to_output(p) for p in plans]
