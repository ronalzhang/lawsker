"""
财务管理相关API端点
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PaymentRecord(BaseModel):
    case_id: str
    amount: float
    payment_method: str


@router.get("/wallet")
async def get_wallet():
    """获取钱包信息"""
    return {"message": "钱包信息获取接口"}


@router.post("/payment")
async def record_payment(payment: PaymentRecord):
    """记录支付"""
    return {"message": "支付记录接口"}


@router.get("/commission")
async def get_commission():
    """获取佣金明细"""
    return {"message": "佣金明细获取接口"} 