"""
财务管理相关API端点
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from fastapi import status as http_status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.deps import get_db, get_current_user, get_config_service
from app.core.config import settings
from app.models.user import User
from app.models.finance import Transaction, CommissionSplit, Wallet, WithdrawalRequest, TransactionStatus, CommissionStatus, PaymentOrder, WithdrawalStatus
from app.services.payment_service import WeChatPayService, CommissionSplitService, WithdrawalService, WeChatPayError, WithdrawalError
from app.services.config_service import SystemConfigService

router = APIRouter()
logger = logging.getLogger(__name__)

# 创建同步数据库引擎（用于服务类）
sync_engine = create_engine(settings.DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)


# Pydantic 模型定义
class PaymentRequest(BaseModel):
    case_id: UUID = Field(..., description="案件ID")
    amount: float = Field(..., gt=0, description="支付金额")
    description: Optional[str] = Field(None, description="支付描述")


class PaymentResponse(BaseModel):
    success: bool
    out_trade_no: str
    qr_code: str
    message: str


class PaymentCallbackRequest(BaseModel):
    out_trade_no: str = Field(..., description="商户订单号")
    transaction_id: str = Field(..., description="微信交易号")
    total_fee: str = Field(..., description="支付金额（分）")
    time_end: str = Field(..., description="支付完成时间")


class WalletResponse(BaseModel):
    user_id: str
    balance: float
    withdrawable_balance: float
    frozen_balance: float
    total_earned: float
    total_withdrawn: float
    commission_count: int
    last_commission_at: Optional[datetime]


class CommissionSummaryResponse(BaseModel):
    total_count: int
    total_amount: float
    average_amount: float
    monthly_trend: List[Dict[str, Any]]


class CommissionDetailResponse(BaseModel):
    id: str
    transaction_id: str
    case_number: str
    role_at_split: str
    amount: float
    percentage: float
    status: str
    created_at: datetime
    paid_at: Optional[datetime]


class CommissionListResponse(BaseModel):
    items: List[CommissionDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WithdrawalCreateRequest(BaseModel):
    """创建提现请求"""
    amount: float = Field(..., gt=0, description="提现金额")
    bank_account: str = Field(..., max_length=255, description="银行账户")
    bank_name: str = Field(..., max_length=100, description="银行名称")
    account_holder: str = Field(..., max_length=100, description="账户姓名")


class WithdrawalResponse(BaseModel):
    """提现响应"""
    id: str
    request_number: str
    amount: float
    fee: float
    actual_amount: float
    status: str
    auto_approved: bool
    estimated_arrival: str


class WithdrawalDetailResponse(BaseModel):
    """提现详情响应"""
    id: str
    request_number: str
    user_id: str
    user_name: str
    amount: float
    fee: float
    actual_amount: float
    bank_account: str
    bank_name: str
    account_holder: str
    status: str
    risk_score: Optional[float]
    auto_approved: bool
    admin_notes: Optional[str]
    created_at: str
    processed_at: Optional[str]


class WithdrawalListResponse(BaseModel):
    """提现列表响应"""
    items: List[WithdrawalDetailResponse]
    total: int
    page: int
    size: int
    pages: int


class WithdrawalApprovalRequest(BaseModel):
    """提现审批请求"""
    admin_notes: Optional[str] = Field(None, description="管理员备注")


class WithdrawalRejectionRequest(BaseModel):
    """提现拒绝请求"""
    admin_notes: str = Field(..., description="拒绝原因")


class TransactionResponse(BaseModel):
    id: str
    case_id: str
    case_number: str
    amount: float
    transaction_type: str
    status: str
    payment_gateway: Optional[str]
    gateway_txn_id: Optional[str]
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("/payment/create", response_model=PaymentResponse)
async def create_payment(
    request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """创建微信支付订单"""
    
    try:
        wechat_service = WeChatPayService(config_service)
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            result = await wechat_service.create_payment_order(
                case_id=request.case_id,
                amount=Decimal(str(request.amount)),
                description=request.description or "律师服务费用",
                user_id=UUID(str(current_user.id)),
                db=sync_session,
                tenant_id=UUID(str(current_user.tenant_id))
            )
            
            return PaymentResponse(
                success=True,
                out_trade_no=result["order_no"],
                qr_code=result["qr_code"],
                message="支付订单创建成功"
            )
            
        finally:
            sync_session.close()
        
    except WeChatPayError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建支付订单失败"
        )


@router.post("/payment/callback")
async def payment_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """微信支付回调处理"""
    
    try:
        wechat_service = WeChatPayService(config_service)
        
        # 获取XML数据
        xml_data = await request.body()
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            result = await wechat_service.handle_payment_callback(
                xml_data=xml_data.decode('utf-8'),
                db=sync_session
            )
            
            return {"status": "success", "message": "回调处理成功"}
            
        finally:
            sync_session.close()
        
    except Exception as e:
        logger.error(f"支付回调处理失败: {str(e)}")
        return {"status": "fail", "message": "回调处理失败"}


@router.get("/wallet", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户钱包信息"""
    
    try:
        from sqlalchemy import select
        
        # 查询用户钱包
        wallet_query = select(Wallet).where(Wallet.user_id == current_user.id)
        wallet_result = await db.execute(wallet_query)
        wallet = wallet_result.scalar_one_or_none()
        
        if not wallet:
            # 如果钱包不存在，创建默认钱包
            wallet = Wallet(
                user_id=current_user.id,
                balance=Decimal("0"),
                withdrawable_balance=Decimal("0"),
                frozen_balance=Decimal("0"),
                total_earned=Decimal("0"),
                total_withdrawn=Decimal("0"),
                commission_count=0
            )
            db.add(wallet)
            await db.commit()
            await db.refresh(wallet)
        
        return WalletResponse(
            user_id=str(wallet.user_id),
            balance=float(wallet.balance),  # type: ignore
            withdrawable_balance=float(wallet.withdrawable_balance),  # type: ignore
            frozen_balance=float(wallet.frozen_balance),  # type: ignore
            total_earned=float(wallet.total_earned),  # type: ignore
            total_withdrawn=float(wallet.total_withdrawn),  # type: ignore
            commission_count=int(wallet.commission_count),  # type: ignore
            last_commission_at=wallet.last_commission_at  # type: ignore
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取钱包信息失败"
        )


@router.get("/commission/summary", response_model=CommissionSummaryResponse)
async def get_commission_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """获取分成汇总信息"""
    
    try:
        commission_service = CommissionSplitService(config_service)
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            summary = commission_service.get_commission_summary(
                user_id=UUID(str(current_user.id)),
                db=sync_session
            )
            
            return CommissionSummaryResponse(
                total_count=summary["total_count"],
                total_amount=summary["total_amount"],
                average_amount=summary["average_amount"],
                monthly_trend=summary["monthly_trend"]
            )
            
        finally:
            sync_session.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分成汇总失败"
        )


@router.get("/commission/details", response_model=CommissionListResponse)
async def get_commission_details(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """获取分成明细列表"""
    
    try:
        commission_service = CommissionSplitService(config_service)
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            details = commission_service.get_commission_details(
                user_id=UUID(str(current_user.id)),
                page=page,
                size=size,
                db=sync_session
            )
            
            items = [
                CommissionDetailResponse(
                    id=item["id"],
                    transaction_id=item["transaction_id"],
                    case_number=item["case_number"],
                    role_at_split=item["role_at_split"],
                    amount=item["amount"],
                    percentage=item["percentage"],
                    status=item["status"],
                    created_at=datetime.fromisoformat(item["created_at"]),
                    paid_at=datetime.fromisoformat(item["paid_at"]) if item["paid_at"] else None
                )
                for item in details["items"]
            ]
            
            return CommissionListResponse(
                items=items,
                total=details["total"],
                page=details["page"],
                page_size=details["page_size"],
                total_pages=details["total_pages"]
            )
            
        finally:
            sync_session.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分成明细失败"
        )


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    transaction_type: Optional[str] = Query(None, description="交易类型过滤"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取交易记录"""
    
    try:
        from sqlalchemy import select, and_, func
        from sqlalchemy.orm import selectinload
        
        # 构建查询条件
        conditions = []
        
        # 查询用户相关的交易（通过案件关联）
        from app.models.case import Case
        conditions.append(Case.tenant_id == current_user.tenant_id)
        
        if transaction_type:
            conditions.append(Transaction.transaction_type == transaction_type)
        if status_filter:
            conditions.append(Transaction.status == status_filter)
        
        # 查询交易列表
        offset = (page - 1) * page_size
        query = select(Transaction).join(Case).options(
            selectinload(Transaction.case)
        ).where(and_(*conditions)).order_by(
            Transaction.created_at.desc()
        ).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        # 查询总数
        count_query = select(func.count()).select_from(Transaction).join(Case).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 构建响应数据
        items = []
        for transaction in transactions:
            items.append(TransactionResponse(
                id=str(transaction.id),
                case_id=str(transaction.case_id),
                case_number=transaction.case.case_number if transaction.case else "未知",  # type: ignore
                amount=float(transaction.amount),  # type: ignore
                transaction_type=transaction.transaction_type.value,  # type: ignore
                status=transaction.status.value,  # type: ignore
                payment_gateway=transaction.payment_gateway,  # type: ignore
                gateway_txn_id=transaction.gateway_txn_id,  # type: ignore
                description=transaction.description,  # type: ignore
                created_at=transaction.created_at,  # type: ignore
                completed_at=transaction.completed_at  # type: ignore
            ))
        
        return TransactionListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取交易记录失败"
        )


@router.post("/withdrawal/create", response_model=WithdrawalResponse)
async def create_withdrawal_request(
    request: WithdrawalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """创建提现申请"""
    
    try:
        withdrawal_service = WithdrawalService(config_service)
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            result = await withdrawal_service.create_withdrawal_request(
                user_id=UUID(str(current_user.id)),
                amount=Decimal(str(request.amount)),
                bank_account=request.bank_account,
                bank_name=request.bank_name,
                account_holder=request.account_holder,
                db=sync_session,
                tenant_id=UUID(str(current_user.tenant_id))
            )
            
            return WithdrawalResponse(
                id=result["id"],
                request_number=result["request_number"],
                amount=result["amount"],
                fee=result["fee"],
                actual_amount=result["actual_amount"],
                status=result["status"],
                auto_approved=result["auto_approved"],
                estimated_arrival=result["estimated_arrival"]
            )
            
        finally:
            sync_session.close()
        
    except WithdrawalError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建提现申请失败"
        )


@router.get("/withdrawal/list", response_model=WithdrawalListResponse)
async def get_user_withdrawal_requests(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """获取用户提现申请列表"""
    
    try:
        withdrawal_service = WithdrawalService(config_service)
        
        # 转换状态参数
        status_filter = None
        if status:
            try:
                status_filter = WithdrawalStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="无效的状态参数"
                )
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            result = await withdrawal_service.get_withdrawal_requests(
                user_id=UUID(str(current_user.id)),
                status=status_filter,
                page=page,
                size=size,
                db=sync_session
            )
            
            items = [
                WithdrawalDetailResponse(
                    id=item["id"],
                    request_number=item["request_number"],
                    user_id=item["user_id"],
                    user_name=item["user_name"],
                    amount=item["amount"],
                    fee=item["fee"],
                    actual_amount=item["actual_amount"],
                    bank_account=item["bank_account"],
                    bank_name=item["bank_name"],
                    account_holder=item["account_holder"],
                    status=item["status"],
                    risk_score=item["risk_score"],
                    auto_approved=item["auto_approved"],
                    admin_notes=item["admin_notes"],
                    created_at=item["created_at"],
                    processed_at=item["processed_at"]
                )
                for item in result["items"]
            ]
            
            return WithdrawalListResponse(
                items=items,
                total=result["total"],
                page=result["page"],
                size=result["size"],
                pages=result["pages"]
            )
            
        finally:
            sync_session.close()
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取提现申请列表失败"
        )


@router.get("/withdrawal/admin/list", response_model=WithdrawalListResponse)
async def get_admin_withdrawal_requests(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """管理员获取所有提现申请列表"""
    
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问"
        )
    
    try:
        withdrawal_service = WithdrawalService(config_service)
        
        # 转换状态参数
        status_filter = None
        if status:
            try:
                status_filter = WithdrawalStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="无效的状态参数"
                )
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            result = await withdrawal_service.get_withdrawal_requests(
                user_id=None,  # 管理员查看所有用户
                status=status_filter,
                page=page,
                size=size,
                db=sync_session
            )
            
            items = [
                WithdrawalDetailResponse(
                    id=item["id"],
                    request_number=item["request_number"],
                    user_id=item["user_id"],
                    user_name=item["user_name"],
                    amount=item["amount"],
                    fee=item["fee"],
                    actual_amount=item["actual_amount"],
                    bank_account=item["bank_account"],
                    bank_name=item["bank_name"],
                    account_holder=item["account_holder"],
                    status=item["status"],
                    risk_score=item["risk_score"],
                    auto_approved=item["auto_approved"],
                    admin_notes=item["admin_notes"],
                    created_at=item["created_at"],
                    processed_at=item["processed_at"]
                )
                for item in result["items"]
            ]
            
            return WithdrawalListResponse(
                items=items,
                total=result["total"],
                page=result["page"],
                size=result["size"],
                pages=result["pages"]
            )
            
        finally:
            sync_session.close()
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取提现申请列表失败"
        )


@router.post("/withdrawal/admin/{withdrawal_id}/approve")
async def approve_withdrawal_request(
    withdrawal_id: UUID,
    request: WithdrawalApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """管理员审批通过提现申请"""
    
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问"
        )
    
    try:
        withdrawal_service = WithdrawalService(config_service)
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            result = await withdrawal_service.approve_withdrawal(
                withdrawal_id=withdrawal_id,
                admin_id=UUID(str(current_user.id)),
                admin_notes=request.admin_notes,
                db=sync_session
            )
            
            return result
            
        finally:
            sync_session.close()
        
    except WithdrawalError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审批提现申请失败"
        )


@router.post("/withdrawal/admin/{withdrawal_id}/reject")
async def reject_withdrawal_request(
    withdrawal_id: UUID,
    request: WithdrawalRejectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """管理员拒绝提现申请"""
    
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问"
        )
    
    try:
        withdrawal_service = WithdrawalService(config_service)
        
        # 使用同步数据库会话
        sync_session = SyncSessionLocal()
        
        try:
            result = await withdrawal_service.reject_withdrawal(
                withdrawal_id=withdrawal_id,
                admin_id=UUID(str(current_user.id)),
                admin_notes=request.admin_notes,
                db=sync_session
            )
            
            return result
            
        finally:
            sync_session.close()
        
    except WithdrawalError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="拒绝提现申请失败"
        )


@router.get("/withdrawal/config")
async def get_withdrawal_config(
    current_user: User = Depends(get_current_user),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """获取提现配置信息"""
    
    try:
        # 获取提现配置
        withdrawal_config = await config_service.get_config("business", "withdrawal_settings")
        if not withdrawal_config:
            withdrawal_config = {
                "min_amount": 10.0,
                "max_amount": 50000.0,
                "daily_limit": 100000.0,
                "fee_rate": 0.001,
                "min_fee": 1.0,
                "max_fee": 50.0,
                "auto_approve_threshold": 1000.0,
                "processing_time": "1-3个工作日"
            }
        
        return {
            "withdrawal_settings": withdrawal_config,
            "available_banks": [
                {"code": "ICBC", "name": "中国工商银行"},
                {"code": "CCB", "name": "中国建设银行"},
                {"code": "ABC", "name": "中国农业银行"},
                {"code": "BOC", "name": "中国银行"},
                {"code": "COMM", "name": "交通银行"},
                {"code": "CMB", "name": "招商银行"},
                {"code": "CITIC", "name": "中信银行"},
                {"code": "CEB", "name": "光大银行"},
                {"code": "CMBC", "name": "民生银行"},
                {"code": "PAB", "name": "平安银行"}
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提现配置失败: {str(e)}"
        )


@router.get("/config")
async def get_finance_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """
    获取财务配置信息（仅管理员）
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问"
        )
    
    try:
        # 获取业务配置
        commission_config = await config_service.get_config("business", "commission_rates")
        if not commission_config:
            commission_config = {
                "lawyer": 0.30,
                "sales": 0.20,
                "platform": 0.50,
                "safety_margin": 0.15
            }
        
        # 获取支付配置状态
        payment_config = await config_service.get_config("payment_keys", "wechat_pay")
        payment_enabled = bool(payment_config and payment_config.get("enabled"))
        
        # 获取提现配置
        withdrawal_config = await config_service.get_config("business", "withdrawal_settings")
        if not withdrawal_config:
            withdrawal_config = {
                "min_amount": 10.0,
                "max_amount": 50000.0,
                "daily_limit": 100000.0,
                "processing_time": "1-3个工作日"
            }
        
        return {
            "commission_rates": commission_config,
            "payment_channels": {
                "wechat_pay": {
                    "enabled": payment_enabled,
                    "name": "微信支付"
                },
                "alipay": {
                    "enabled": False,
                    "name": "支付宝"
                }
            },
            "withdrawal_settings": withdrawal_config
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取财务配置失败: {str(e)}"
        ) 