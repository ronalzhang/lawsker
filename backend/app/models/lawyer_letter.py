"""
律师函服务相关数据模型
包含律师函订单、模板、发送记录等模型
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from decimal import Decimal

from app.core.database import Base


class LetterType(enum.Enum):
    """律师函类型枚举"""
    DEBT_COLLECTION = "debt_collection"    # 催收函
    DEMAND_LETTER = "demand_letter"        # 催告函
    WARNING_LETTER = "warning_letter"      # 警告函
    CEASE_DESIST = "cease_desist"         # 停止侵权函
    BREACH_NOTICE = "breach_notice"        # 违约通知函
    CUSTOM = "custom"                      # 自定义


class LetterUrgency(enum.Enum):
    """紧急程度枚举"""
    NORMAL = "normal"      # 普通（48小时内）
    URGENT = "urgent"      # 加急（24小时内）
    EMERGENCY = "emergency"  # 紧急（1小时内）


class OrderStatus(enum.Enum):
    """订单状态枚举"""
    DRAFT = "draft"                # 草稿
    PENDING_PAYMENT = "pending_payment"  # 待支付
    PAID = "paid"                  # 已支付
    GENERATING = "generating"      # 生成中
    PENDING_REVIEW = "pending_review"  # 待审核
    APPROVED = "approved"          # 已审核
    SENDING = "sending"            # 发送中
    SENT = "sent"                  # 已发送
    DELIVERED = "delivered"        # 已送达
    FAILED = "failed"              # 失败
    CANCELLED = "cancelled"        # 已取消


class SendMethod(enum.Enum):
    """发送方式枚举"""
    EMAIL = "email"        # 邮件
    SMS = "sms"           # 短信
    WECHAT = "wechat"     # 微信
    POSTAL = "postal"     # 邮寄
    COURIER = "courier"   # 快递


class LawyerLetterOrder(Base):
    """律师函订单表"""
    __tablename__ = "lawyer_letter_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)  # 订单编号
    
    # 客户信息
    client_name = Column(String(100), nullable=False)      # 客户姓名
    client_phone = Column(String(20), nullable=False)      # 客户电话
    client_email = Column(String(255), nullable=True)      # 客户邮箱
    client_company = Column(String(200), nullable=True)    # 客户公司
    
    # 目标方信息
    target_name = Column(String(100), nullable=False)      # 对方姓名/公司名
    target_phone = Column(String(20), nullable=True)       # 对方电话
    target_email = Column(String(255), nullable=True)      # 对方邮箱
    target_address = Column(Text, nullable=True)           # 对方地址
    
    # 律师函信息
    letter_type = Column(SQLEnum(LetterType), nullable=False)
    urgency = Column(SQLEnum(LetterUrgency), default=LetterUrgency.NORMAL, nullable=False)
    title = Column(String(200), nullable=False)            # 标题
    content_brief = Column(Text, nullable=False)           # 内容简述
    case_background = Column(Text, nullable=True)          # 案件背景
    legal_basis = Column(Text, nullable=True)              # 法律依据
    demands = Column(JSONB, nullable=True)                 # 具体要求JSON数组
    
    # AI生成内容
    ai_generated_content = Column(Text, nullable=True)     # AI生成的完整内容
    ai_template_id = Column(UUID(as_uuid=True), ForeignKey("lawyer_letter_templates.id"), nullable=True)
    customizations = Column(JSONB, nullable=True)          # 个性化修改JSON
    
    # 分配信息
    assigned_lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # 发送信息
    send_method = Column(SQLEnum(SendMethod), nullable=False)
    scheduled_send_time = Column(DateTime(timezone=True), nullable=True)  # 定时发送时间
    actual_send_time = Column(DateTime(timezone=True), nullable=True)     # 实际发送时间
    delivery_confirmation = Column(Boolean, default=False)  # 送达确认
    
    # 订单状态和金额
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.DRAFT, nullable=False)
    amount = Column(String(10), nullable=False)            # 金额（存储为字符串避免精度问题）
    payment_method = Column(String(50), nullable=True)     # 支付方式
    paid_at = Column(DateTime(timezone=True), nullable=True)  # 支付时间
    
    # 备注和附件
    notes = Column(Text, nullable=True)                    # 备注
    attachments = Column(JSONB, nullable=True)             # 附件JSON数组
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    
    # 关联关系
    assigned_lawyer = relationship("User", foreign_keys=[assigned_lawyer_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])
    template = relationship("LawyerLetterTemplate", back_populates="orders")
    send_records = relationship("LetterSendRecord", back_populates="order")
    review_tasks = relationship("DocumentReviewTask", back_populates="lawyer_letter_order")

    def __repr__(self):
        return f"<LawyerLetterOrder(id={self.id}, order_number={self.order_number}, status={self.status.value}, amount={self.amount})>"


class LawyerLetterTemplate(Base):
    """律师函模板表"""
    __tablename__ = "lawyer_letter_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)             # 模板名称
    letter_type = Column(SQLEnum(LetterType), nullable=False)
    category = Column(String(50), nullable=True)           # 分类
    
    # 模板内容
    title_template = Column(Text, nullable=False)          # 标题模板
    content_template = Column(Text, nullable=False)        # 内容模板
    variables = Column(JSONB, nullable=True)               # 变量定义JSON
    legal_clauses = Column(JSONB, nullable=True)           # 法条引用JSON
    
    # 模板属性
    is_active = Column(Boolean, default=True)              # 是否启用
    is_premium = Column(Boolean, default=False)            # 是否高级模板
    suggested_price = Column(String(10), nullable=True)    # 建议价格
    usage_count = Column(Integer, default=0)               # 使用次数
    success_rate = Column(Integer, default=0)              # 成功率百分比
    
    # 审核信息
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    creator = relationship("User", foreign_keys=[created_by_id])
    approver = relationship("User", foreign_keys=[approved_by_id])
    orders = relationship("LawyerLetterOrder", back_populates="template")

    def __repr__(self):
        return f"<LawyerLetterTemplate(id={self.id}, name={self.name}, letter_type={self.letter_type.value}, is_active={self.is_active})>"


class LetterSendRecord(Base):
    """律师函发送记录表"""
    __tablename__ = "letter_send_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("lawyer_letter_orders.id"), nullable=False)
    
    # 发送信息
    send_method = Column(SQLEnum(SendMethod), nullable=False)
    recipient = Column(String(255), nullable=False)        # 接收方（邮箱/手机号等）
    sender_info = Column(JSONB, nullable=True)             # 发送方信息JSON
    
    # 发送内容
    subject = Column(String(200), nullable=True)           # 邮件主题/短信标题
    content = Column(Text, nullable=False)                 # 发送内容
    attachments = Column(JSONB, nullable=True)             # 附件信息JSON
    
    # 发送状态
    send_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    delivery_status = Column(String(50), default='sent')   # 投递状态
    delivery_time = Column(DateTime(timezone=True), nullable=True)  # 投递时间
    read_time = Column(DateTime(timezone=True), nullable=True)      # 阅读时间
    
    # 回执信息
    delivery_receipt = Column(JSONB, nullable=True)        # 投递回执JSON
    read_receipt = Column(Boolean, default=False)          # 是否已读
    response_received = Column(Boolean, default=False)     # 是否收到回复
    response_content = Column(Text, nullable=True)         # 回复内容
    
    # 错误信息
    error_message = Column(Text, nullable=True)            # 错误信息
    retry_count = Column(Integer, default=0)               # 重试次数
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    order = relationship("LawyerLetterOrder", back_populates="send_records")

    def __repr__(self):
        return f"<LetterSendRecord(id={self.id}, order_id={self.order_id}, send_method={self.send_method.value}, delivery_status={self.delivery_status})>" 