"""create_admin_logging_settings_table

Revision ID: 9878c1fccc84
Revises: 45a2d7c5cb7f
Create Date: 2025-05-25 23:13:16.497332

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # For UUID type


# revision identifiers, used by Alembic.
revision = '9878c1fccc84'
down_revision = '45a2d7c5cb7f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'admin_logging_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')), # Assuming gen_random_uuid() for server-side default generation
        sa.Column('setting_name', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('admin_logging_settings')
