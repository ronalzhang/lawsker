"""
财务相关数据模型
支持支付、提现、钱包等功能
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class PaymentStatus(enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"      # 待支付
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"    # 已退款


class PaymentMethod(enum.Enum):
    """支付方式枚举"""
    WECHAT = "wechat"        # 微信支付
    ALIPAY = "alipay"        # 支付宝
    BANK_TRANSFER = "bank_transfer"  # 银行转账
    CREDIT_CARD = "credit_card"  # 信用卡


class WithdrawalStatus(enum.Enum):
    """提现状态枚举"""
    PENDING = "pending"      # 待处理
    PROCESSING = "processing"  # 处理中
    APPROVED = "approved"    # 已批准
    REJECTED = "rejected"    # 已拒绝
    COMPLETED = "completed"  # 已完成


class Payment(Base):
    """支付记录表"""
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    
    # 支付信息
    payment_number = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)  # 支付金额
    currency = Column(String(3), default="CNY", nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    
    # 状态信息
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    gateway_transaction_id = Column(String(100), nullable=True)  # 网关交易ID
    
    # 网关响应
    gateway_response = Column(Text, nullable=True)  # 网关响应数据JSON (字符串)
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)  # 支付时间
    
    # 关联关系
    user = relationship("User")
    case = relationship("Case")

    def __repr__(self):
        return f"<Payment(id={self.id}, payment_number={self.payment_number}, status={self.status.value})>"


class Wallet(Base):
    """钱包表"""
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # 余额信息
    balance = Column(Numeric(15, 2), default=0, nullable=False)  # 当前余额
    frozen_balance = Column(Numeric(15, 2), default=0, nullable=False)  # 冻结余额
    
    # 统计信息
    total_income = Column(Numeric(15, 2), default=0, nullable=False)  # 总收入
    total_expense = Column(Numeric(15, 2), default=0, nullable=False)  # 总支出
    
    # 状态信息
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User")

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, balance={self.balance})>"


class Transaction(Base):
    """交易记录表"""
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    
    # 交易信息
    transaction_type = Column(String(50), nullable=False)  # income, expense, transfer
    amount = Column(Numeric(15, 2), nullable=False)  # 交易金额
    currency = Column(String(3), default="CNY", nullable=False)
    
    # 交易详情
    description = Column(Text, nullable=True)  # 交易描述
    reference_id = Column(String(100), nullable=True)  # 关联ID（支付ID、提现ID等）
    reference_type = Column(String(50), nullable=True)  # 关联类型
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联关系
    wallet = relationship("Wallet")
    case = relationship("Case")

    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"


class WithdrawalRequest(Base):
    """提现申请表"""
    __tablename__ = "withdrawal_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 提现信息
    request_number = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)  # 提现金额
    currency = Column(String(3), default="CNY", nullable=False)
    
    # 收款信息
    bank_name = Column(String(100), nullable=True)  # 银行名称
    bank_account = Column(String(50), nullable=True)  # 银行账号
    account_holder = Column(String(100), nullable=True)  # 账户持有人
    
    # 状态信息
    status = Column(SQLEnum(WithdrawalStatus), nullable=False, default=WithdrawalStatus.PENDING)
    admin_notes = Column(Text, nullable=True)  # 管理员备注
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)  # 处理时间
    
    # 关联关系
    user = relationship("User")

    def __repr__(self):
        return f"<WithdrawalRequest(id={self.id}, request_number={self.request_number}, status={self.status.value})>"


class BillingRecord(Base):
    """计费记录表"""
    __tablename__ = "billing_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 计费信息
    billing_number = Column(String(100), unique=True, nullable=False, index=True)
    service_type = Column(String(50), nullable=False)  # 服务类型
    amount = Column(Numeric(15, 2), nullable=False)  # 计费金额
    currency = Column(String(3), default="CNY", nullable=False)
    
    # 计费详情
    billing_period = Column(String(20), nullable=True)  # 计费周期
    usage_quantity = Column(Integer, nullable=True)  # 使用量
    unit_price = Column(Numeric(10, 4), nullable=True)  # 单价
    
    # 元数据
    request_metadata = Column(Text, nullable=False, default="{}")  # 元数据JSON (字符串)
    
    # 状态信息
    is_paid = Column(Boolean, default=False, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)  # 支付时间
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User")

    def __repr__(self):
        return f"<BillingRecord(id={self.id}, billing_number={self.billing_number}, amount={self.amount})>" 