"""adiciona voter_goal em tenants

Revision ID: 0019_add_tenant_voter_goal
Revises: 0018_voter_creator_nullable
Create Date: 2026-08-17

Meta de eleitores da campanha, usada no painel do início (barra de
progresso). Opcional — sem meta definida, o painel mostra só a contagem.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019_add_tenant_voter_goal"
down_revision: str | None = "0018_voter_creator_nullable"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("voter_goal", sa.Integer(), nullable=True))
    op.create_check_constraint("ck_tenants_voter_goal_positive", "tenants", "voter_goal > 0")


def downgrade() -> None:
    op.drop_constraint("ck_tenants_voter_goal_positive", "tenants", type_="check")
    op.drop_column("tenants", "voter_goal")
