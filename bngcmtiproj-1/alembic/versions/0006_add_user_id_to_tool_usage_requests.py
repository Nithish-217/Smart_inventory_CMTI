"""
Add user_id column to tool_usage_requests table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0010_add_user_id_to_tool_usage_requests'
down_revision = '0009_add_requested_qty_to_tool_usage_requests'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    table_name = 'tool_usage_requests'
    result = conn.execute(sa.text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='user_id'"))
    if not result.fetchone():
        op.add_column(table_name, sa.Column('user_id', sa.Integer, nullable=False))

def downgrade():
    op.drop_column('tool_usage_requests', 'user_id')
