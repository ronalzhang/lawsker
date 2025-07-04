"""add wechat payment support

Revision ID: 006_add_wechat_payment_support
Revises: 005_update_config_system
Create Date: 2024-01-15 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_wechat_payment_support'
down_revision = '005_update_config_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加微信支付支持的数据库结构优化"""
    
    # 为交易表添加索引优化
    op.create_index(
        'ix_transactions_case_id', 
        'transactions', 
        ['case_id']
    )
    op.create_index(
        'ix_transactions_payment_gateway', 
        'transactions', 
        ['payment_gateway']
    )
    op.create_index(
        'ix_transactions_status_created', 
        'transactions', 
        ['status', 'created_at']
    )
    op.create_index(
        'ix_transactions_gateway_txn_id', 
        'transactions', 
        ['gateway_txn_id'],
        unique=True
    )
    
    # 为分账表添加索引优化
    op.create_index(
        'ix_commission_splits_user_id', 
        'commission_splits', 
        ['user_id']
    )
    op.create_index(
        'ix_commission_splits_transaction_id', 
        'commission_splits', 
        ['transaction_id']
    )
    op.create_index(
        'ix_commission_splits_status_paid', 
        'commission_splits', 
        ['status', 'paid_at']
    )
    op.create_index(
        'ix_commission_splits_role_created', 
        'commission_splits', 
        ['role_at_split', 'created_at']
    )
    
    # 为钱包表添加索引优化
    op.create_index(
        'ix_wallets_balance', 
        'wallets', 
        ['balance']
    )
    op.create_index(
        'ix_wallets_last_commission', 
        'wallets', 
        ['last_commission_at']
    )
    
    # 添加支付订单表（用于跟踪支付状态）
    op.create_table(
        'payment_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  default=sa.text('gen_random_uuid()')),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('order_number', sa.String(100), unique=True, nullable=False),
        sa.Column('amount', sa.DECIMAL(18, 2), nullable=False),
        sa.Column('currency', sa.String(10), default='CNY', nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=False),  # wechat, alipay, etc.
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('qr_code_url', sa.Text, nullable=True),
        sa.Column('gateway_order_id', sa.String(255), nullable=True),
        sa.Column('gateway_response', postgresql.JSONB, nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # 为支付订单表添加索引
    op.create_index('ix_payment_orders_case_id', 'payment_orders', ['case_id'])
    op.create_index('ix_payment_orders_user_id', 'payment_orders', ['user_id'])
    op.create_index('ix_payment_orders_order_number', 'payment_orders', ['order_number'], unique=True)
    op.create_index('ix_payment_orders_status', 'payment_orders', ['status'])
    op.create_index('ix_payment_orders_gateway_order_id', 'payment_orders', ['gateway_order_id'])
    op.create_index('ix_payment_orders_created_at', 'payment_orders', ['created_at'])
    
    # 添加提现申请表
    op.create_table(
        'withdrawal_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('wallets.user_id'), nullable=False),
        sa.Column('request_number', sa.String(100), unique=True, nullable=False),
        sa.Column('amount', sa.DECIMAL(18, 2), nullable=False),
        sa.Column('fee', sa.DECIMAL(18, 2), default=0, nullable=False),
        sa.Column('actual_amount', sa.DECIMAL(18, 2), nullable=False),
        sa.Column('bank_account', sa.String(255), nullable=True),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('account_holder', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('admin_notes', sa.Text, nullable=True),
        sa.Column('processed_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # 为提现申请表添加索引
    op.create_index('ix_withdrawal_requests_user_id', 'withdrawal_requests', ['user_id'])
    op.create_index('ix_withdrawal_requests_status', 'withdrawal_requests', ['status'])
    op.create_index('ix_withdrawal_requests_created_at', 'withdrawal_requests', ['created_at'])
    op.create_index('ix_withdrawal_requests_processed_at', 'withdrawal_requests', ['processed_at'])
    
    # 添加分账规则配置表
    op.create_table(
        'commission_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('rule_name', sa.String(100), nullable=False),
        sa.Column('case_type', sa.String(50), nullable=True),
        sa.Column('amount_range_min', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('amount_range_max', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('platform_rate', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('lawyer_rate', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('sales_rate', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('safety_margin', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('priority', sa.Integer, default=0, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # 为分账规则表添加索引
    op.create_index('ix_commission_rules_tenant_id', 'commission_rules', ['tenant_id'])
    op.create_index('ix_commission_rules_case_type', 'commission_rules', ['case_type'])
    op.create_index('ix_commission_rules_priority', 'commission_rules', ['priority'])
    op.create_index('ix_commission_rules_is_active', 'commission_rules', ['is_active'])


def downgrade() -> None:
    """回滚微信支付支持的数据库更改"""
    
    # 删除分账规则表
    op.drop_table('commission_rules')
    
    # 删除提现申请表
    op.drop_table('withdrawal_requests')
    
    # 删除支付订单表
    op.drop_table('payment_orders')
    
    # 删除钱包表索引
    op.drop_index('ix_wallets_last_commission', table_name='wallets')
    op.drop_index('ix_wallets_balance', table_name='wallets')
    
    # 删除分账表索引
    op.drop_index('ix_commission_splits_role_created', table_name='commission_splits')
    op.drop_index('ix_commission_splits_status_paid', table_name='commission_splits')
    op.drop_index('ix_commission_splits_transaction_id', table_name='commission_splits')
    op.drop_index('ix_commission_splits_user_id', table_name='commission_splits')
    
    # 删除交易表索引
    op.drop_index('ix_transactions_gateway_txn_id', table_name='transactions')
    op.drop_index('ix_transactions_status_created', table_name='transactions')
    op.drop_index('ix_transactions_payment_gateway', table_name='transactions')
    op.drop_index('ix_transactions_case_id', table_name='transactions') 