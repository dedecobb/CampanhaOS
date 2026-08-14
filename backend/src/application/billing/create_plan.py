from src.application.billing.dto import CreatePlanInput, PlanOutput
from src.application.billing.mapper import plan_to_output
from src.domain.billing.entities import Plan
from src.domain.billing.repository import PlanRepository


class CreatePlanUseCase:
    def __init__(self, plan_repository: PlanRepository) -> None:
        self._plan_repository = plan_repository

    async def execute(self, input_data: CreatePlanInput) -> PlanOutput:
        plan = Plan.create(
            name=input_data.name,
            price=input_data.price,
            max_users=input_data.max_users,
            max_voters=input_data.max_voters,
        )
        await self._plan_repository.save(plan)
        return plan_to_output(plan)
