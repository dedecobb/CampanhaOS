from src.application.billing.dto import GetPlanInput, PlanOutput
from src.application.billing.exceptions import PlanNotFoundError
from src.application.billing.mapper import plan_to_output
from src.domain.billing.repository import PlanRepository


class GetPlanUseCase:
    def __init__(self, plan_repository: PlanRepository) -> None:
        self._plan_repository = plan_repository

    async def execute(self, input_data: GetPlanInput) -> PlanOutput:
        plan = await self._plan_repository.find_by_id(input_data.plan_id)
        if plan is None:
            raise PlanNotFoundError
        return plan_to_output(plan)
