"""empty message

Revision ID: b69afb65d5df
Revises: de201b4a0423
Create Date: 2020-11-20 18:43:52.269966

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b69afb65d5df'
down_revision = 'de201b4a0423'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game', sa.Column('state_json_uni', sa.UnicodeText(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('game', 'state_json_uni')
    # ### end Alembic commands ###