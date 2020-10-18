"""empty message

Revision ID: cbe4d53bbf84
Revises: 
Create Date: 2020-10-18 11:32:42.335575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cbe4d53bbf84'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('base_card',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('json', sa.Text(), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_base_card_name'), 'base_card', ['name'], unique=False)
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('slack_id', sa.String(length=50), nullable=True),
    sa.Column('last_pick_timestamp', sa.DateTime(), nullable=True),
    sa.Column('last_notif_timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_name'), 'user', ['name'], unique=True)
    op.create_table('cube',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('style', sa.Enum('standard', 'legacy', name='cubestyle'), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cube_active'), 'cube', ['active'], unique=False)
    op.create_index(op.f('ix_cube_timestamp'), 'cube', ['timestamp'], unique=False)
    op.create_table('achievement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cube_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('conditions', sa.Text(), nullable=True),
    sa.Column('unlock', sa.Text(), nullable=True),
    sa.Column('multiunlock', sa.Boolean(), nullable=True),
    sa.Column('version', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('created_timestamp', sa.DateTime(), nullable=True),
    sa.Column('unlocked_by_id', sa.Integer(), nullable=True),
    sa.Column('unlocked_timestamp', sa.DateTime(), nullable=True),
    sa.Column('finalized_timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['cube_id'], ['cube.id'], ),
    sa.ForeignKeyConstraint(['unlocked_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cube_card',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('version', sa.Integer(), nullable=True),
    sa.Column('latest', sa.Boolean(), nullable=True),
    sa.Column('json', sa.Text(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('latest_id', sa.Integer(), nullable=True),
    sa.Column('cube_id', sa.Integer(), nullable=True),
    sa.Column('base_id', sa.Integer(), nullable=True),
    sa.Column('added_by_id', sa.Integer(), nullable=True),
    sa.Column('edited_by_id', sa.Integer(), nullable=True),
    sa.Column('removed_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['added_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['base_id'], ['base_card.id'], ),
    sa.ForeignKeyConstraint(['cube_id'], ['cube.id'], ),
    sa.ForeignKeyConstraint(['edited_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['removed_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cube_card_timestamp'), 'cube_card', ['timestamp'], unique=False)
    op.create_table('draft',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('pack_size', sa.Integer(), nullable=True),
    sa.Column('num_packs', sa.Integer(), nullable=True),
    sa.Column('num_seats', sa.Integer(), nullable=True),
    sa.Column('scar_rounds_str', sa.String(length=64), nullable=True),
    sa.Column('cube_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['cube_id'], ['cube.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_draft_timestamp'), 'draft', ['timestamp'], unique=False)
    op.create_table('match_result',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('opponent_id', sa.Integer(), nullable=False),
    sa.Column('draft_id', sa.Integer(), nullable=False),
    sa.Column('wins', sa.Integer(), nullable=True),
    sa.Column('losses', sa.Integer(), nullable=True),
    sa.Column('draws', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['draft_id'], ['draft.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_match_result_opponent_id'), 'match_result', ['opponent_id'], unique=False)
    op.create_table('pack',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('draft_id', sa.Integer(), nullable=True),
    sa.Column('seat_number', sa.Integer(), nullable=True),
    sa.Column('pack_number', sa.Integer(), nullable=True),
    sa.Column('scarred_this_round_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['draft_id'], ['draft.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('scar',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cube_id', sa.Integer(), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('restrictions', sa.String(length=128), nullable=True),
    sa.Column('errata', sa.Text(), nullable=True),
    sa.Column('created_timestamp', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('applied_timestamp', sa.DateTime(), nullable=True),
    sa.Column('applied_by_id', sa.Integer(), nullable=True),
    sa.Column('applied_to_id', sa.Integer(), nullable=True),
    sa.Column('removed_timestamp', sa.DateTime(), nullable=True),
    sa.Column('removed_by_id', sa.Integer(), nullable=True),
    sa.Column('locked_by_id', sa.Integer(), nullable=True),
    sa.Column('locked_pack_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['applied_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['applied_to_id'], ['cube_card.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['cube_id'], ['cube.id'], ),
    sa.ForeignKeyConstraint(['removed_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('seat',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('draft_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['draft_id'], ['draft.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pack_card',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('card_id', sa.Integer(), nullable=True),
    sa.Column('draft_id', sa.Integer(), nullable=True),
    sa.Column('pack_id', sa.Integer(), nullable=True),
    sa.Column('picked_by_id', sa.Integer(), nullable=True),
    sa.Column('pick_number', sa.Integer(), nullable=True),
    sa.Column('picked_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['card_id'], ['cube_card.id'], ),
    sa.ForeignKeyConstraint(['draft_id'], ['draft.id'], ),
    sa.ForeignKeyConstraint(['pack_id'], ['pack.id'], ),
    sa.ForeignKeyConstraint(['picked_by_id'], ['seat.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pack_card')
    op.drop_table('seat')
    op.drop_table('scar')
    op.drop_table('pack')
    op.drop_index(op.f('ix_match_result_opponent_id'), table_name='match_result')
    op.drop_table('match_result')
    op.drop_index(op.f('ix_draft_timestamp'), table_name='draft')
    op.drop_table('draft')
    op.drop_index(op.f('ix_cube_card_timestamp'), table_name='cube_card')
    op.drop_table('cube_card')
    op.drop_table('achievement')
    op.drop_index(op.f('ix_cube_timestamp'), table_name='cube')
    op.drop_index(op.f('ix_cube_active'), table_name='cube')
    op.drop_table('cube')
    op.drop_index(op.f('ix_user_name'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_base_card_name'), table_name='base_card')
    op.drop_table('base_card')
    # ### end Alembic commands ###