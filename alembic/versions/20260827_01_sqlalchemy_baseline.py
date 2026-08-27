"""SQLAlchemy baseline for application-owned database tables.

Revision ID: 20260827_01
Revises:
Create Date: 2026-08-27
"""
from alembic import op
import sqlalchemy as sa


revision = "20260827_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adopt the Django schema without replacing any existing tables.

    Deployments already have these tables from Django migrations.  This
    baseline intentionally creates only missing tables, then records the
    Alembic revision; it never rebuilds a table or touches its data.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("authentication_user"):
        op.create_table(
            "authentication_user",
            sa.Column("password", sa.String(length=128), nullable=False),
            sa.Column("last_login", sa.DateTime(), nullable=True),
            sa.Column("is_superuser", sa.Boolean(), nullable=False),
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=150), nullable=False),
            sa.Column("email", sa.String(length=254), nullable=False, unique=True),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("is_staff", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    if not inspector.has_table("token_blacklist_outstandingtoken"):
        op.create_table(
            "token_blacklist_outstandingtoken",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("token", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("jti", sa.String(length=255), nullable=False, unique=True),
            sa.Column(
                "user_id",
                sa.BigInteger(),
                sa.ForeignKey(
                    "authentication_user.id", deferrable=True, initially="DEFERRED"
                ),
                nullable=True,
            ),
        )
        op.create_index(
            "token_blacklist_outstandingtoken_user_id_83bc629a",
            "token_blacklist_outstandingtoken",
            ["user_id"],
        )

    if not inspector.has_table("token_blacklist_blacklistedtoken"):
        op.create_table(
            "token_blacklist_blacklistedtoken",
            sa.Column("blacklisted_at", sa.DateTime(), nullable=False),
            sa.Column(
                "token_id",
                sa.BigInteger(),
                sa.ForeignKey(
                    "token_blacklist_outstandingtoken.id",
                    deferrable=True,
                    initially="DEFERRED",
                ),
                nullable=False,
                unique=True,
            ),
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        )

    if not inspector.has_table("meals"):
        op.create_table(
            "meals",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("title", sa.String(length=100), nullable=False),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("image_url", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_meals_id", "meals", ["id"])


def downgrade() -> None:
    # This adoption baseline must never drop tables that may predate Alembic.
    pass
