"""empty message

Revision ID: 1fd285330a4d
Revises: 3fa4aa040bf8
Create Date: 2020-10-19 09:03:44.794070

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1fd285330a4d'
down_revision = '3fa4aa040bf8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('achievement', sa.Column('story', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('achievement', 'story')
    # ### end Alembic commands ###
