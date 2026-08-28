"""add category to meal_options

Revision ID: 9c93119a9d65
Revises: 20260827_01
Create Date: 2026-08-28 03:22:51.953128
"""
from alembic import op
import sqlalchemy as sa

revision = '9c93119a9d65'
down_revision = '20260827_01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('meal_options', sa.Column('category', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('meal_options', 'category')
