"""Add AI document review and lawyer workload models

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '004_add_ai_review_models'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建文档审核任务表
    op.create_table('document_review_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), default=uuid.uuid4, primary_key=True),
        sa.Column('task_number', sa.String(50), unique=True, nullable=False, index=True, comment="任务编号"),
        
        # 关联信息
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=True, comment="关联案件ID"),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lawyer_letter_orders.id'), nullable=True, comment="关联订单ID"),
        sa.Column('lawyer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, comment="分配律师ID"),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, comment="创建者ID"),
        
        # 文档信息
        sa.Column('document_type', sa.String(50), nullable=False, comment="文档类型"),
        sa.Column('original_content', sa.Text, nullable=False, comment="AI生成的原始内容"),
        sa.Column('current_content', sa.Text, nullable=False, comment="当前内容（可能经过修改）"),
        sa.Column('final_content', sa.Text, nullable=True, comment="最终确认内容"),
        
        # 审核信息
        sa.Column('status', sa.Enum('pending', 'in_review', 'approved', 'rejected', 'modification_requested', 'modified', 'authorized', 'sent', 'cancelled', name='reviewstatus'), default='pending', comment="审核状态"),
        sa.Column('priority', sa.Integer, default=1, comment="优先级（1-5，5最高）"),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True, comment="截止时间"),
        
        # AI生成元数据
        sa.Column('ai_metadata', postgresql.JSON, nullable=True, comment="AI生成元数据"),
        sa.Column('generation_prompt', sa.Text, nullable=True, comment="生成提示词"),
        sa.Column('ai_providers', postgresql.JSON, nullable=True, comment="使用的AI提供商"),
        
        # 审核记录
        sa.Column('review_notes', sa.Text, nullable=True, comment="审核备注"),
        sa.Column('modification_requests', sa.Text, nullable=True, comment="修改要求"),
        sa.Column('approval_notes', sa.Text, nullable=True, comment="通过备注"),
        sa.Column('rejection_reason', sa.Text, nullable=True, comment="拒绝原因"),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment="创建时间"),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True, comment="审核时间"),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True, comment="通过时间"),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True, comment="发送时间"),
        
        # 业务配置
        sa.Column('auto_approve', sa.Boolean, default=False, comment="是否自动通过"),
        sa.Column('requires_signature', sa.Boolean, default=True, comment="是否需要律师签名"),
        
        comment="文档审核任务表"
    )

    # 创建文档审核日志表
    op.create_table('document_review_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), default=uuid.uuid4, primary_key=True),
        sa.Column('review_task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_review_tasks.id'), nullable=False, comment="审核任务ID"),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, comment="操作人ID"),
        
        # 操作信息
        sa.Column('action', sa.String(50), nullable=False, comment="操作类型"),
        sa.Column('old_status', sa.Enum('pending', 'in_review', 'approved', 'rejected', 'modification_requested', 'modified', 'authorized', 'sent', 'cancelled', name='reviewstatus'), nullable=True, comment="原状态"),
        sa.Column('new_status', sa.Enum('pending', 'in_review', 'approved', 'rejected', 'modification_requested', 'modified', 'authorized', 'sent', 'cancelled', name='reviewstatus'), nullable=False, comment="新状态"),
        
        # 详细信息
        sa.Column('comment', sa.Text, nullable=True, comment="操作说明"),
        sa.Column('content_changes', postgresql.JSON, nullable=True, comment="内容变更记录"),
        sa.Column('attachment_files', postgresql.JSON, nullable=True, comment="附件文件"),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment="操作时间"),
        
        comment="文档审核日志表"
    )

    # 创建律师工作负荷表
    op.create_table('lawyer_workloads',
        sa.Column('id', postgresql.UUID(as_uuid=True), default=uuid.uuid4, primary_key=True),
        sa.Column('lawyer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True, comment="律师ID"),
        
        # 工作负荷统计
        sa.Column('active_cases', sa.Integer, default=0, comment="活跃案件数"),
        sa.Column('pending_reviews', sa.Integer, default=0, comment="待审核文档数"),
        sa.Column('daily_capacity', sa.Integer, default=10, comment="日处理能力"),
        sa.Column('weekly_capacity', sa.Integer, default=50, comment="周处理能力"),
        
        # 质量指标
        sa.Column('average_review_time', sa.Integer, default=0, comment="平均审核时间（分钟）"),
        sa.Column('approval_rate', sa.Integer, default=95, comment="通过率（百分比）"),
        sa.Column('client_satisfaction', sa.Integer, default=90, comment="客户满意度（百分比）"),
        
        # 可用性
        sa.Column('is_available', sa.Boolean, default=True, comment="是否可接新任务"),
        sa.Column('max_concurrent_tasks', sa.Integer, default=20, comment="最大并发任务数"),
        sa.Column('current_workload_score', sa.Integer, default=0, comment="当前工作负荷评分"),
        
        # 专业领域
        sa.Column('specialties', postgresql.JSON, nullable=True, comment="专业领域"),
        sa.Column('preferred_document_types', postgresql.JSON, nullable=True, comment="偏好文档类型"),
        
        # 时间统计
        sa.Column('last_assignment_at', sa.DateTime(timezone=True), nullable=True, comment="最后分配时间"),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
        
        comment="律师工作负荷表"
    )

    # 创建索引
    op.create_index('idx_review_tasks_status', 'document_review_tasks', ['status'])
    op.create_index('idx_review_tasks_lawyer_id', 'document_review_tasks', ['lawyer_id'])
    op.create_index('idx_review_tasks_case_id', 'document_review_tasks', ['case_id'])
    op.create_index('idx_review_tasks_deadline', 'document_review_tasks', ['deadline'])
    op.create_index('idx_review_tasks_priority', 'document_review_tasks', ['priority'])
    
    op.create_index('idx_review_logs_task_id', 'document_review_logs', ['review_task_id'])
    op.create_index('idx_review_logs_reviewer_id', 'document_review_logs', ['reviewer_id'])
    op.create_index('idx_review_logs_action', 'document_review_logs', ['action'])
    
    op.create_index('idx_lawyer_workloads_available', 'lawyer_workloads', ['is_available'])
    op.create_index('idx_lawyer_workloads_score', 'lawyer_workloads', ['current_workload_score'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_lawyer_workloads_score')
    op.drop_index('idx_lawyer_workloads_available')
    op.drop_index('idx_review_logs_action')
    op.drop_index('idx_review_logs_reviewer_id')
    op.drop_index('idx_review_logs_task_id')
    op.drop_index('idx_review_tasks_priority')
    op.drop_index('idx_review_tasks_deadline')
    op.drop_index('idx_review_tasks_case_id')
    op.drop_index('idx_review_tasks_lawyer_id')
    op.drop_index('idx_review_tasks_status')
    
    # 删除表
    op.drop_table('lawyer_workloads')
    op.drop_table('document_review_logs')
    op.drop_table('document_review_tasks')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS reviewstatus CASCADE') 