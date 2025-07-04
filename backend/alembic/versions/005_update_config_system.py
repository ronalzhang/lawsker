"""update config system

Revision ID: 005_update_config_system
Revises: 004_add_ai_review_models
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_update_config_system'
down_revision = '004_add_ai_review_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""
    
    # 检查system_configs表是否存在，如果不存在则创建
    # 注意：在实际的PostgreSQL中，这个表可能已经存在
    
    # 确保JSONB列可以存储加密的配置值
    # 添加is_active列用于软删除
    try:
        op.add_column('system_configs', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    except Exception:
        # 列可能已经存在
        pass
    
    # 添加配置值类型和范围限制列
    try:
        op.add_column('system_configs', sa.Column('min_value', sa.String(50), nullable=True))
        op.add_column('system_configs', sa.Column('max_value', sa.String(50), nullable=True))
        op.add_column('system_configs', sa.Column('is_editable', sa.Boolean(), nullable=False, server_default='true'))
    except Exception:
        # 列可能已经存在
        pass
    
    # 创建配置类别的索引
    try:
        op.create_index('idx_system_configs_category', 'system_configs', ['category'])
        op.create_index('idx_system_configs_tenant_category', 'system_configs', ['tenant_id', 'category'])
        op.create_index('idx_system_configs_active', 'system_configs', ['is_active'])
    except Exception:
        # 索引可能已经存在
        pass


def downgrade() -> None:
    """降级数据库结构"""
    
    # 删除索引
    try:
        op.drop_index('idx_system_configs_active', table_name='system_configs')
        op.drop_index('idx_system_configs_tenant_category', table_name='system_configs')
        op.drop_index('idx_system_configs_category', table_name='system_configs')
    except Exception:
        pass
    
    # 删除新添加的列
    try:
        op.drop_column('system_configs', 'is_editable')
        op.drop_column('system_configs', 'max_value')
        op.drop_column('system_configs', 'min_value')
        op.drop_column('system_configs', 'is_active')
    except Exception:
        pass 