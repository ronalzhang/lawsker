"""
简化文书库API端点
使用模板生成，避免数据库依赖
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.simple_document_service import SimpleDocumentService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()


class DocumentGenerationRequest(BaseModel):
    task_id: str
    task_type: str = "lawyer_letter"
    task_title: str
    task_description: str
    amount: Optional[float] = 0
    overdue_days: Optional[int] = 0
    force_regenerate: bool = False


@router.post("/generate")
async def generate_document(
    request: DocumentGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    生成文书内容（简化版本）
    """
    try:
        # 初始化服务
        doc_service = SimpleDocumentService()
        user_service = UserService(db)
        
        # 构建任务信息
        task_info = {
            'taskId': request.task_id,
            'taskType': request.task_type,
            'title': request.task_title,
            'description': request.task_description,
            'amount': request.amount or 0,
            'overdue_days': request.overdue_days or 0,
            'budget': request.amount or 0
        }
        
        # 获取律师信息
        try:
            lawyer_user = await user_service.get_user_by_id(current_user["id"])
            
            lawyer_info = {
                'name': lawyer_user.full_name if lawyer_user and lawyer_user.full_name else lawyer_user.username if lawyer_user else '张律师',
                'license_number': '11010201234567890',  # 默认律师证号
                'phone': lawyer_user.phone_number if lawyer_user and lawyer_user.phone_number else '138-0000-0000',
                'email': lawyer_user.email if lawyer_user else 'lawyer@lawfirm.com'
            }
        except Exception as e:
            logger.warning(f"获取律师信息失败，使用默认信息: {str(e)}")
            lawyer_info = doc_service.get_default_lawyer_info()
        
        # 使用默认律所信息（实际项目中应从配置或数据库获取）
        law_firm_info = doc_service.get_default_law_firm_info()
        
        # 生成文书
        result = await doc_service.generate_lawyer_letter(
            task_info=task_info,
            lawyer_info=lawyer_info,
            law_firm_info=law_firm_info
        )
        
        if result.get('success'):
            return {
                "success": True,
                "document": {
                    "title": result.get('title'),
                    "content": result.get('content'),
                    "document_type": result.get('document_type', 'lawyer_letter'),
                    "quality_score": result.get('quality_score', 95),
                    "generation_method": result.get('generation_method', 'template'),
                    "lawyer_info": {
                        "name": lawyer_info['name'],
                        "phone": lawyer_info['phone']
                    },
                    "law_firm_info": {
                        "name": law_firm_info['name'],
                        "address": law_firm_info['address']
                    }
                },
                "message": "文书生成成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文书生成失败: {result.get('error', '未知错误')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文书处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文书处理失败: {str(e)}"
        )


@router.get("/templates")
async def get_document_templates():
    """获取可用的文书模板"""
    return {
        "success": True,
        "templates": [
            {
                "type": "lawyer_letter",
                "name": "催收律师函",
                "description": "用于债务催收的律师函模板",
                "available": True
            },
            {
                "type": "debt_collection",
                "name": "债务催收通知书",
                "description": "正式的债务催收通知书",
                "available": False
            }
        ]
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "success": True,
        "service": "document_library_simple",
        "status": "healthy",
        "message": "简化文书服务运行正常"
    }