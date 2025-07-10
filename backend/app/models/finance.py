"""
财务相关数据模型
包含交易、分账、钱包等模型
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, DECIMAL, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class TransactionType(enum.Enum):
    """交易类型枚举"""
    PAYMENT = "payment"    # 回款
    REFUND = "refund"      # 退款
    PAYOUT = "payout"      # 分账支出


class TransactionStatus(enum.Enum):
    """交易状态枚举"""
    PENDING = "pending"      # 待处理
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败


class CommissionStatus(enum.Enum):
    """分账状态枚举"""
    PENDING = "pending"  # 待分账
    PAID = "paid"        # 已支付
    FAILED = "failed"    # 失败


class WithdrawalStatus(enum.Enum):
    """提现状态枚举"""
    PENDING = "pending"        # 待审核
    APPROVED = "approved"      # 已批准
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 已完成
    REJECTED = "rejected"      # 已拒绝
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"    # 已取消


class Transaction(Base):
    """交易流水表"""
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    
    # 交易信息
    amount = Column(DECIMAL(18, 2), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    
    # 支付信息
    payment_gateway = Column(String(50), nullable=True)     # 支付渠道
    gateway_txn_id = Column(String(255), unique=True, nullable=True)  # 支付网关交易号
    gateway_response = Column(JSONB, nullable=True)         # 网关响应数据
    
    # 业务信息
    description = Column(String(500), nullable=True)        # 交易描述
    notes = Column(String(1000), nullable=True)             # 备注
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    
    # 关联关系
    case = relationship("Case", back_populates="transactions")
    commission_splits = relationship("CommissionSplit", back_populates="transaction")

    def __repr__(self):
        return f"<Transaction(id={self.id}, case_id={self.case_id}, type={self.transaction_type.value}, amount={self.amount}, status={self.status.value})>"


class CommissionSplit(Base):
    """分账记录表"""
    __tablename__ = "commission_splits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 分账信息
    role_at_split = Column(String(50), nullable=False)      # 分账时的角色
    amount = Column(DECIMAL(18, 2), nullable=False)         # 分账金额
    percentage = Column(DECIMAL(5, 4), nullable=False)      # 分账比例
    status = Column(SQLEnum(CommissionStatus), default=CommissionStatus.PENDING, nullable=False)
    
    # 支付信息
    payout_method = Column(String(50), nullable=True)       # 支付方式
    payout_account = Column(String(255), nullable=True)     # 支付账户
    payout_txn_id = Column(String(255), nullable=True)      # 支付交易号
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)  # 支付时间
    
    # 关联关系
    transaction = relationship("Transaction", back_populates="commission_splits")
    user = relationship("User")

    def __repr__(self):
        return f"<CommissionSplit(id={self.id}, user_id={self.user_id}, role={self.role_at_split}, amount={self.amount}, status={self.status.value})>"


class PaymentOrder(Base):
    """支付订单表"""
    __tablename__ = "payment_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(100), unique=True, nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 订单信息
    amount = Column(DECIMAL(18, 2), nullable=False)
    description = Column(String(500), nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, paid, expired, cancelled
    
    # 微信支付信息
    prepay_id = Column(String(100), nullable=True)
    code_url = Column(String(500), nullable=True)  # 二维码链接
    transaction_id = Column(String(100), nullable=True)  # 微信交易号
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    case = relationship("Case")
    user = relationship("User")

    def __repr__(self):
        return f"<PaymentOrder(order_no={self.order_no}, amount={self.amount}, status={self.status})>"


class Wallet(Base):
    """用户钱包表"""
    __tablename__ = "wallets"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    
    # 余额信息
    balance = Column(DECIMAL(18, 2), nullable=False, default=0)                    # 账户余额
    withdrawable_balance = Column(DECIMAL(18, 2), nullable=False, default=0)       # 可提现余额
    frozen_balance = Column(DECIMAL(18, 2), nullable=False, default=0)             # 冻结余额
    total_earned = Column(DECIMAL(18, 2), nullable=False, default=0)               # 累计收入
    total_withdrawn = Column(DECIMAL(18, 2), nullable=False, default=0)            # 累计提现
    
    # 统计信息
    commission_count = Column(DECIMAL(10, 0), nullable=False, default=0)           # 分账次数
    last_commission_at = Column(DateTime(timezone=True), nullable=True)            # 最后分账时间
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="wallet")
    # withdrawal_requests relationship removed due to foreign key conflicts

    def __repr__(self):
        return f"<Wallet(user_id={self.user_id}, balance={self.balance}, withdrawable={self.withdrawable_balance})>"


class WithdrawalRequest(Base):
    """提现申请表"""
    __tablename__ = "withdrawal_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 申请信息
    request_number = Column(String(100), unique=True, nullable=False)       # 申请单号
    amount = Column(DECIMAL(18, 2), nullable=False)                         # 申请金额
    fee = Column(DECIMAL(18, 2), default=0, nullable=False)                 # 手续费
    actual_amount = Column(DECIMAL(18, 2), nullable=False)                  # 实际到账金额
    
    # 银行信息
    bank_account = Column(String(255), nullable=False)                      # 银行账户
    bank_name = Column(String(100), nullable=False)                         # 银行名称
    account_holder = Column(String(100), nullable=False)                    # 账户姓名
    
    # 状态和审核
    status = Column(SQLEnum(WithdrawalStatus), default=WithdrawalStatus.PENDING, nullable=False)
    admin_notes = Column(Text, nullable=True)                               # 管理员备注
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # 处理人
    processed_at = Column(DateTime(timezone=True), nullable=True)           # 处理时间
    
    # 租户信息
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    
    # 风控信息
    risk_score = Column(DECIMAL(5, 2), nullable=True)                       # 风险评分
    auto_approved = Column(Boolean, default=False)                          # 是否自动审批
    
    # 元数据
    request_metadata = Column(JSONB, nullable=False, default=dict)          # 元数据
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id])
    # wallet relationship removed due to foreign key conflicts - use user.wallet instead
    admin_user = relationship("User", foreign_keys=[admin_id])

    def __repr__(self):
        return f"<WithdrawalRequest(id={self.id}, request_number={self.request_number}, amount={self.amount}, status={self.status.value})>" 