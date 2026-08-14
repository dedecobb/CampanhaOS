from src.application.billing.dto import PlanOutput, SubscriptionOutput
from src.domain.billing.entities import Plan, Subscription


def plan_to_output(plan: Plan) -> PlanOutput:
    return PlanOutput(
        id=plan.id,
        name=plan.name,
        price=plan.price,
        max_users=plan.max_users,
        max_voters=plan.max_voters,
        is_active=plan.is_active,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def subscription_to_output(subscription: Subscription) -> SubscriptionOutput:
    return SubscriptionOutput(
        id=subscription.id,
        tenant_id=subscription.tenant_id,
        plan_id=subscription.plan_id,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )
