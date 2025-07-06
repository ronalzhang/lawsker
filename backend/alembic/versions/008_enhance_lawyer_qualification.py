"""enhance lawyer qualification table

Revision ID: 008_enhance_lawyer_qualification
Revises: 007_add_missing_tables
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_enhance_lawyer_qualification'
down_revision = '007_add_missing_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加律师基本信息字段
    op.add_column('lawyer_qualifications', sa.Column('lawyer_name', sa.String(100), nullable=False, server_default=''))
    op.add_column('lawyer_qualifications', sa.Column('gender', sa.String(10), nullable=True))
    op.add_column('lawyer_qualifications', sa.Column('id_card_number', sa.String(18), nullable=True))
    
    # 添加认证文件信息字段
    op.add_column('lawyer_qualifications', sa.Column('license_image_url', sa.String(500), nullable=True))
    op.add_column('lawyer_qualifications', sa.Column('license_image_metadata', postgresql.JSONB(), nullable=True))
    
    # 添加AI验证相关字段
    op.add_column('lawyer_qualifications', sa.Column('ai_verification_score', sa.Integer, default=0, nullable=False))
    op.add_column('lawyer_qualifications', sa.Column('ai_extraction_result', postgresql.JSONB(), nullable=True))
    
    # 创建索引
    op.create_index('idx_lawyer_qualifications_id_card', 'lawyer_qualifications', ['id_card_number'])
    op.create_index('idx_lawyer_qualifications_name', 'lawyer_qualifications', ['lawyer_name'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_lawyer_qualifications_name', table_name='lawyer_qualifications')
    op.drop_index('idx_lawyer_qualifications_id_card', table_name='lawyer_qualifications')
    
    # 删除添加的字段
    op.drop_column('lawyer_qualifications', 'ai_extraction_result')
    op.drop_column('lawyer_qualifications', 'ai_verification_score')
    op.drop_column('lawyer_qualifications', 'license_image_metadata')
    op.drop_column('lawyer_qualifications', 'license_image_url')
    op.drop_column('lawyer_qualifications', 'id_card_number')
    op.drop_column('lawyer_qualifications', 'gender')
    op.drop_column('lawyer_qualifications', 'lawyer_name') 