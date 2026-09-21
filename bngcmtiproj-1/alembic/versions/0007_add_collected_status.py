"""add collected status

Revision ID: 0011_add_collected_status
Revises: 0010_add_user_id_to_tool_usage_requests
Create Date: 2025-08-25 13:09:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011_add_collected_status'
down_revision = '0010_add_user_id_to_tool_usage_requests'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add COLLECTED to the RequestStatus enum
    op.execute("ALTER TYPE requeststatus ADD VALUE 'COLLECTED'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave this as a no-op
    pass
