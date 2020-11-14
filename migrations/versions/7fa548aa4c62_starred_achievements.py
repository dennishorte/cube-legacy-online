"""Starred Achievements

Revision ID: 7fa548aa4c62
Revises: 4e29e7bbdfb7
Create Date: 2020-11-10 18:38:51.442471

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fa548aa4c62'
down_revision = '4e29e7bbdfb7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('achievement_star',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('ach_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['ach_id'], ['achievement.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('achievement_star')
    # ### end Alembic commands ###