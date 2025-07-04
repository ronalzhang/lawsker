"""
案件管理相关API端点
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class CaseCreate(BaseModel):
    client_id: str
    debtor_name: str
    case_amount: float
    description: Optional[str] = None


@router.get("/")
async def get_cases():
    """获取案件列表"""
    return {"message": "案件列表获取接口"}


@router.post("/")
async def create_case(case_data: CaseCreate):
    """创建新案件"""
    return {"message": "案件创建接口"}


@router.get("/{case_id}")
async def get_case(case_id: str):
    """获取案件详情"""
    return {"message": f"案件详情获取接口: {case_id}"} 