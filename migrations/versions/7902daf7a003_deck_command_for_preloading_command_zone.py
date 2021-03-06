"""Deck.command for preloading command zone

Revision ID: 7902daf7a003
Revises: 2f399ab5d2a3
Create Date: 2021-01-12 19:03:01.185288

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7902daf7a003'
down_revision = '2f399ab5d2a3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('deck', sa.Column('command_ids', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('deck', 'command_ids')
    # ### end Alembic commands ###
