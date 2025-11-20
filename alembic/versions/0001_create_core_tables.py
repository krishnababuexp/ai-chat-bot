"""create core tables
Revises:
Create Date: 2025-11-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg


# revision identifiers, used by Alembic.
revision = '0001_create_core_tables'
down_revision = None
branch_labels = None
depends_on = None




def upgrade():
op.create_table(
'sites',
sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
sa.Column('name', sa.Text, nullable=False),
sa.Column('domain', sa.Text, nullable=False, unique=True),
sa.Column('api_key', sa.Text, nullable=True),
sa.Column('language', sa.Text, nullable=True),
sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
)


op.create_table(
'pages',
sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
sa.Column('site_id', pg.UUID(as_uuid=True), sa.ForeignKey('sites.id', ondelete='CASCADE'), nullable=False),
sa.Column('url', sa.Text, nullable=False),
sa.Column('title', sa.Text, nullable=True),
sa.Column('content', sa.Text, nullable=True),
sa.Column('content_hash', sa.Text, nullable=True),
sa.Column('word_count', sa.Integer, nullable=True),
sa.Column('http_status', sa.Integer, nullable=True),
sa.Column('status', sa.SmallInteger, nullable=True, server_default='0'),
sa.Column('last_crawled_at', sa.DateTime(timezone=True), nullable=True),
sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
)


op.create_table(
'page_chunks',
sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
sa.Column('page_id', pg.UUID(as_uuid=True), sa.ForeignKey('pages.id', ondelete='CASCADE'), nullable=False),
sa.Column('chunk_index', sa.Integer, nullable=False),
sa.Column('chunk_text', sa.Text, nullable=False),
sa.Column('token_count', sa.Integer, nullable=True),
sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
)


op.create_table(
'index_jobs',
sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
sa.Column('site_id', pg.UUID(as_uuid=True), sa.ForeignKey('sites.id', ondelete='SET NULL'), nullable=True),
sa.Column('job_type', sa.Text, nullable=True),
sa.Column('status', sa.Text, nullable=True),
sa.Column('message', sa.Text, nullable=True),
sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
)




def downgrade():
op.drop_table('index_jobs')
op.drop_table('page_chunks')
op.drop_table('pages')
op.drop_table('sites')