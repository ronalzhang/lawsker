"""
财务管理相关API端点
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, get_config_service
from app.models.user import User
from app.models.finance import Transaction, CommissionSplit, Wallet, TransactionStatus, CommissionStatus, PaymentOrder
from app.services.payment_service import WeChatPayService, CommissionSplitService, WeChatPayError
from app.services.config_service import SystemConfigService

router = APIRouter()


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


class WithdrawalRequest(BaseModel):
    """提现请求"""
    amount: Decimal = Field(..., gt=0, description="提现金额")
    bank_account: str = Field(..., max_length=50, description="银行账户")
    bank_name: str = Field(..., max_length=100, description="银行名称")
    account_name: str = Field(..., max_length=100, description="账户姓名")


@router.post("/payment/create", response_model=PaymentResponse)
async def create_payment(
    payment_request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """创建支付订单"""
    
    try:
        wechat_service = WeChatPayService(db, config_service)
        
        # 生成回调URL（实际部署时需要配置真实域名）
        notify_url = "https://api.lawsker.com/api/v1/finance/payment/callback"
        
        result = await wechat_service.create_payment_order(
            case_id=payment_request.case_id,
            amount=Decimal(str(payment_request.amount)),
            body=payment_request.description or f"案件支付",
            notify_url=notify_url,
            tenant_id=current_user.tenant_id
        )
        
        return PaymentResponse(
            success=True,
            out_trade_no=result["out_trade_no"],
            qr_code=result["qr_code"],
            message="支付订单创建成功"
        )
        
    except WeChatPayError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建支付订单失败"
        )


@router.post("/payment/callback")
async def handle_payment_callback(
    callback_data: PaymentCallbackRequest,
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """处理微信支付回调"""
    
    try:
        wechat_service = WeChatPayService(db, config_service)
        
        # 转换回调数据格式
        payment_data = {
            "out_trade_no": callback_data.out_trade_no,
            "transaction_id": callback_data.transaction_id,
            "total_fee": callback_data.total_fee,
            "time_end": callback_data.time_end
        }
        
        result = await wechat_service.handle_payment_callback(payment_data)
        
        return {"return_code": "SUCCESS", "return_msg": "OK"}
        
    except WeChatPayError as e:
        return {"return_code": "FAIL", "return_msg": str(e)}
    except Exception as e:
        return {"return_code": "FAIL", "return_msg": "处理回调失败"}


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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取钱包信息失败"
        )


@router.get("/commission/summary", response_model=CommissionSummaryResponse)
async def get_commission_summary(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """获取用户分账汇总"""
    
    try:
        commission_service = CommissionSplitService(db, config_service)
        
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        summary = await commission_service.get_commission_summary(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 生成月度趋势数据（简化版本）
        monthly_trend = []
        for i in range(min(days // 30, 12)):
            month_start = end_date - timedelta(days=(i+1)*30)
            month_end = end_date - timedelta(days=i*30)
            monthly_trend.append({
                "month": month_start.strftime("%Y-%m"),
                "amount": summary["total_amount"] / max(days // 30, 1),  # 简化计算
                "count": summary["total_count"] // max(days // 30, 1)
            })
        
        return CommissionSummaryResponse(
            total_count=summary["total_count"],
            total_amount=summary["total_amount"],
            average_amount=summary["average_amount"],
            monthly_trend=monthly_trend
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分账汇总失败"
        )


@router.get("/commission/details", response_model=CommissionListResponse)
async def get_commission_details(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """获取用户分账明细"""
    
    try:
        commission_service = CommissionSplitService(db, config_service)
        
        result = await commission_service.get_commission_details(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )
        
        # 构建响应数据
        items = []
        for split in result["items"]:
            items.append(CommissionDetailResponse(
                id=str(split.id),
                transaction_id=str(split.transaction_id),
                case_number=split.transaction.case.case_number if split.transaction and split.transaction.case else "未知",  # type: ignore
                role_at_split=split.role_at_split,  # type: ignore
                amount=float(split.amount),  # type: ignore
                percentage=float(split.percentage),  # type: ignore
                status=split.status.value,  # type: ignore
                created_at=split.created_at,  # type: ignore
                paid_at=split.paid_at  # type: ignore
            ))
        
        return CommissionListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分账明细失败"
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取交易记录失败"
        )


@router.post("/wallet/withdraw")
async def request_withdrawal(
    request: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """申请提现"""
    
    try:
        from sqlalchemy import select
        
        # 查询用户钱包
        wallet_query = select(Wallet).where(Wallet.user_id == current_user.id)
        wallet_result = await db.execute(wallet_query)
        wallet = wallet_result.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="钱包不存在"
            )
        
        # 检查余额
        if float(wallet.withdrawable_balance) < float(request.amount):  # type: ignore
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="可提现余额不足"
            )
        
        # 这里应该调用实际的提现处理逻辑
        # 目前只返回成功响应
        return {
            "success": True,
            "message": "提现申请已提交，请等待处理",
            "amount": float(request.amount),
            "estimated_arrival": "1-3个工作日"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提现申请失败"
        )


@router.get("/config")
async def get_finance_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取财务配置信息（仅管理员）
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
            "withdrawal_settings": {
                "min_amount": 10.0,
                "max_amount": 50000.0,
                "daily_limit": 100000.0,
                "processing_time": "1-3个工作日"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取财务配置失败: {str(e)}"
        ) 