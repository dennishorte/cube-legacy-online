"""Add an achievement draft link model

Revision ID: 702428af1717
Revises: fd1a597243f9
Create Date: 2020-11-13 14:29:01.661038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '702428af1717'
down_revision = 'fd1a597243f9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('achievement_draft_link',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('draft_id', sa.Integer(), nullable=False),
    sa.Column('ach_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['ach_id'], ['achievement.id'], ),
    sa.ForeignKeyConstraint(['draft_id'], ['draft.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('achievement_draft_link')
    # ### end Alembic commands ###