"""
AI服务相关API端点
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DocumentRequest(BaseModel):
    case_id: str
    template_type: str
    parameters: dict


@router.post("/generate-document")
async def generate_document(request: DocumentRequest):
    """AI文档生成"""
    return {"message": "AI文档生成接口"}


@router.get("/risk-assessment/{case_id}")
async def risk_assessment(case_id: str):
    """AI风险评估"""
    return {"message": f"AI风险评估接口: {case_id}"} 