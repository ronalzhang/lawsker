"""
财务相关数据模型
包含交易、分账、钱包等模型
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, DECIMAL
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

    def __repr__(self):
        return f"<Wallet(user_id={self.user_id}, balance={self.balance}, withdrawable={self.withdrawable_balance})>" 