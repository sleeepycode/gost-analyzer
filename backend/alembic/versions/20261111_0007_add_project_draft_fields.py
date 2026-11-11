"""add project source type and draft status

Revision ID: 20261111_0007
Revises: 20260520_0006
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20261111_0007"
down_revision = "20260520_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE project_status ADD VALUE IF NOT EXISTS 'draft'")

    op.add_column("projects", sa.Column("source_type", sa.String(length=16), nullable=True))
    op.execute("UPDATE projects SET source_type = 'docx' WHERE source_type IS NULL")
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column("source_type", nullable=False)
        batch_op.alter_column("source_filename", existing_type=sa.String(), nullable=True)
        batch_op.alter_column("source_path", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE projects SET source_filename = '' WHERE source_filename IS NULL")
    op.execute("UPDATE projects SET source_path = '' WHERE source_path IS NULL")
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column("source_filename", existing_type=sa.String(), nullable=False)
        batch_op.alter_column("source_path", existing_type=sa.String(), nullable=False)
    op.drop_column("projects", "source_type")
