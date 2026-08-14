"""
Implementação concreta de FinanceRepository usando SQLAlchemy async.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.finance.entities import FinanceTransaction
from src.domain.finance.repository import FinanceFilter, FinancePage, FinanceRepository, FinanceSummary
from src.infrastructure.database.models import FinanceTransactionModel


class SqlAlchemyFinanceRepository(FinanceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, transaction: FinanceTransaction) -> None:
        existing = await self._session.get(FinanceTransactionModel, transaction.id)
        if existing is None:
            model = FinanceTransactionModel(
                id=transaction.id,
                tenant_id=transaction.tenant_id,
                created_by_user_id=transaction.created_by_user_id,
                type=transaction.type,
                category=transaction.category,
                amount=transaction.amount,
                description=transaction.description,
                occurred_at=transaction.occurred_at,
                deleted_at=transaction.deleted_at,
            )
            self._session.add(model)
        else:
            existing.type = transaction.type
            existing.category = transaction.category
            existing.amount = transaction.amount
            existing.description = transaction.description
            existing.occurred_at = transaction.occurred_at
            existing.deleted_at = transaction.deleted_at

        await self._session.flush()

    async def find_by_id(self, tenant_id: UUID, transaction_id: UUID) -> FinanceTransaction | None:
        stmt = select(FinanceTransactionModel).where(
            FinanceTransactionModel.id == transaction_id,
            FinanceTransactionModel.tenant_id == tenant_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _build_conditions(self, tenant_id: UUID, filters: FinanceFilter) -> list[ColumnElement[bool]]:
        conditions = [FinanceTransactionModel.tenant_id == tenant_id]

        if not filters.include_deleted:
            conditions.append(FinanceTransactionModel.deleted_at.is_(None))
        if filters.type:
            conditions.append(FinanceTransactionModel.type == filters.type)
        if filters.category:
            conditions.append(FinanceTransactionModel.category.ilike(f"%{filters.category}%"))
        if filters.occurred_after:
            conditions.append(FinanceTransactionModel.occurred_at >= filters.occurred_after)
        if filters.occurred_before:
            conditions.append(FinanceTransactionModel.occurred_at <= filters.occurred_before)

        return conditions

    async def list_paginated(
        self,
        tenant_id: UUID,
        filters: FinanceFilter,
        page: int,
        page_size: int,
    ) -> FinancePage:
        conditions = self._build_conditions(tenant_id, filters)

        count_stmt = select(func.count()).select_from(FinanceTransactionModel).where(*conditions)
        total = (await self._session.execute(count_stmt)).scalar_one()

        list_stmt = (
            select(FinanceTransactionModel)
            .where(*conditions)
            .order_by(FinanceTransactionModel.occurred_at.desc(), FinanceTransactionModel.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = (await self._session.execute(list_stmt)).scalars().all()

        return FinancePage(
            items=[self._to_domain(m) for m in models],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_summary(self, tenant_id: UUID, filters: FinanceFilter) -> FinanceSummary:
        conditions = self._build_conditions(tenant_id, filters)

        # Uma query só, agregando por tipo — o banco soma, não o Python.
        stmt = (
            select(FinanceTransactionModel.type, func.coalesce(func.sum(FinanceTransactionModel.amount), 0))
            .where(*conditions)
            .group_by(FinanceTransactionModel.type)
        )
        rows = (await self._session.execute(stmt)).all()
        totals_by_type: dict[str, Decimal] = {row[0]: row[1] for row in rows}

        return FinanceSummary(
            total_receitas=totals_by_type.get("receita", Decimal("0")),
            total_despesas=totals_by_type.get("despesa", Decimal("0")),
            total_doacoes=totals_by_type.get("doacao", Decimal("0")),
        )

    def _to_domain(self, model: FinanceTransactionModel) -> FinanceTransaction:
        return FinanceTransaction(
            id=model.id,
            tenant_id=model.tenant_id,
            created_by_user_id=model.created_by_user_id,
            type=model.type,
            category=model.category,
            amount=model.amount,
            description=model.description,
            occurred_at=model.occurred_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
