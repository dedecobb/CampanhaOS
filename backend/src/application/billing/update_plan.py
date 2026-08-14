from src.application.billing.dto import UNSET, PlanOutput, UpdatePlanInput
from src.application.billing.exceptions import PlanNotFoundError
from src.application.billing.mapper import plan_to_output
from src.domain.billing.repository import PlanRepository


class UpdatePlanUseCase:
    def __init__(self, plan_repository: PlanRepository) -> None:
        self._plan_repository = plan_repository

    async def execute(self, input_data: UpdatePlanInput) -> PlanOutput:
        plan = await self._plan_repository.find_by_id(input_data.plan_id)
        if plan is None:
            raise PlanNotFoundError

        # Mesmo padrão de sentinela do Plan (Bloco A): só repassa
        # max_users/max_voters se o request de fato os mencionou.
        limit_kwargs = {}
        if input_data.max_users is not UNSET:
            limit_kwargs["max_users"] = input_data.max_users
        if input_data.max_voters is not UNSET:
            limit_kwargs["max_voters"] = input_data.max_voters

        plan.update_details(name=input_data.name, price=input_data.price, **limit_kwargs)
        await self._plan_repository.save(plan)
        return plan_to_output(plan)
