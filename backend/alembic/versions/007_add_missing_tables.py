"""add missing tables for complete system

Revision ID: 007_add_missing_tables
Revises: 006_add_wechat_payment_support
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_missing_tables'
down_revision = '006_add_wechat_payment_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加系统完整性所需的缺失表"""
    
    # 添加案件日志表
    op.create_table(
        'case_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  default=sa.text('gen_random_uuid()')),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),  # created, assigned, updated, completed
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('new_values', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False)
    )
    
    # 为案件日志表添加索引
    op.create_index('ix_case_logs_case_id', 'case_logs', ['case_id'])
    op.create_index('ix_case_logs_user_id', 'case_logs', ['user_id'])
    op.create_index('ix_case_logs_action_type', 'case_logs', ['action_type'])
    op.create_index('ix_case_logs_created_at', 'case_logs', ['created_at'])
    
    # 添加系统统计表
    op.create_table(
        'system_statistics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  default=sa.text('gen_random_uuid()')),
        sa.Column('stat_date', sa.Date, nullable=False),
        sa.Column('total_cases', sa.Integer, default=0, nullable=False),
        sa.Column('active_cases', sa.Integer, default=0, nullable=False),
        sa.Column('completed_cases', sa.Integer, default=0, nullable=False),
        sa.Column('total_users', sa.Integer, default=0, nullable=False),
        sa.Column('active_lawyers', sa.Integer, default=0, nullable=False),
        sa.Column('active_sales', sa.Integer, default=0, nullable=False),
        sa.Column('total_transactions', sa.Integer, default=0, nullable=False),
        sa.Column('total_amount', sa.DECIMAL(18, 2), default=0, nullable=False),
        sa.Column('total_commissions', sa.DECIMAL(18, 2), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # 为统计表添加索引
    op.create_index('ix_system_statistics_stat_date', 'system_statistics', ['stat_date'], unique=True)
    op.create_index('ix_system_statistics_created_at', 'system_statistics', ['created_at'])
    
    # 添加用户活动日志表
    op.create_table(
        'user_activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False)
    )
    
    # 为用户活动日志表添加索引
    op.create_index('ix_user_activity_logs_user_id', 'user_activity_logs', ['user_id'])
    op.create_index('ix_user_activity_logs_action', 'user_activity_logs', ['action'])
    op.create_index('ix_user_activity_logs_resource', 'user_activity_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_user_activity_logs_created_at', 'user_activity_logs', ['created_at'])
    op.create_index('ix_user_activity_logs_session_id', 'user_activity_logs', ['session_id'])
    
    # 添加销售数据上传记录表
    op.create_table(
        'data_upload_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('data_type', sa.String(50), nullable=False),  # debt_collection, client_data, etc.
        sa.Column('total_records', sa.Integer, nullable=False),
        sa.Column('processed_records', sa.Integer, default=0, nullable=False),
        sa.Column('failed_records', sa.Integer, default=0, nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('error_details', postgresql.JSONB, nullable=True),
        sa.Column('processing_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 为数据上传记录表添加索引
    op.create_index('ix_data_upload_records_user_id', 'data_upload_records', ['user_id'])
    op.create_index('ix_data_upload_records_data_type', 'data_upload_records', ['data_type'])
    op.create_index('ix_data_upload_records_status', 'data_upload_records', ['status'])
    op.create_index('ix_data_upload_records_created_at', 'data_upload_records', ['created_at'])
    
    # 添加任务发布记录表
    op.create_table(
        'task_publish_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),  # lawyer_letter, debt_collection, contract_review
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('target_info', postgresql.JSONB, nullable=False),  # 目标对象信息
        sa.Column('amount', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('urgency', sa.String(20), default='normal', nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('completion_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 为任务发布记录表添加索引
    op.create_index('ix_task_publish_records_user_id', 'task_publish_records', ['user_id'])
    op.create_index('ix_task_publish_records_task_type', 'task_publish_records', ['task_type'])
    op.create_index('ix_task_publish_records_status', 'task_publish_records', ['status'])
    op.create_index('ix_task_publish_records_assigned_to', 'task_publish_records', ['assigned_to'])
    op.create_index('ix_task_publish_records_created_at', 'task_publish_records', ['created_at'])


def downgrade() -> None:
    """回滚缺失表的添加"""
    
    # 删除任务发布记录表
    op.drop_table('task_publish_records')
    
    # 删除数据上传记录表
    op.drop_table('data_upload_records')
    
    # 删除用户活动日志表
    op.drop_table('user_activity_logs')
    
    # 删除系统统计表
    op.drop_table('system_statistics')
    
    # 删除案件日志表
    op.drop_table('case_logs') 