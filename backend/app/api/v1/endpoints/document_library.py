"""
文书库管理API端点
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.document_library_service import DocumentLibraryService
from app.services.config_service import SystemConfigService
from app.services.ai_service import AIDocumentService
from app.services.email_service import create_email_service

router = APIRouter()


class DocumentGenerationRequest(BaseModel):
    task_id: Optional[str] = None
    case_id: Optional[UUID] = None
    task_type: str = "general_legal"
    task_title: str = ""
    task_description: str = ""
    amount: Optional[float] = None
    overdue_days: Optional[int] = None
    force_regenerate: bool = False


class DocumentUsageFeedback(BaseModel):
    document_id: UUID
    was_successful: bool
    client_response: Optional[str] = None
    modifications_made: Optional[str] = None
    final_content: Optional[str] = None


@router.post("/generate")
async def generate_document(
    request: DocumentGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    生成或获取文书内容
    优先从库中获取，如无合适文书则生成新的
    """
    try:
        # 初始化服务
        config_service = SystemConfigService(db)
        ai_service = AIDocumentService(config_service)
        doc_service = DocumentLibraryService(config_service, ai_service)
        
        # 构建任务信息
        task_info = {
            'taskId': request.task_id,
            'taskType': request.task_type,
            'title': request.task_title,
            'description': request.task_description,
            'amount': request.amount or 0,
            'overdue_days': request.overdue_days or 0
        }
        
        # 获取或生成文书
        result = await doc_service.get_or_generate_document(
            db=db,
            task_info=task_info,
            user_id=current_user["id"],
            case_id=request.case_id,
            force_regenerate=request.force_regenerate
        )
        
        if result['success']:
            return {
                "success": True,
                "document_content": result['document_content'],
                "document_title": result['document_title'],
                "source": result['source'],
                "document_id": str(result['document_id']),
                "usage_stats": {
                    "usage_count": result.get('usage_count', 0),
                    "success_rate": result.get('success_rate', 0),
                    "quality_score": result.get('quality_score', 0)
                },
                "message": result.get('message', '文书生成成功')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', '文书生成失败')
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文书生成服务异常: {str(e)}"
        )


@router.post("/feedback")
async def submit_document_feedback(
    feedback: DocumentUsageFeedback,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交文书使用反馈
    用于改进文书质量和成功率统计
    """
    try:
        from sqlalchemy import text
        
        # 更新使用历史记录
        update_sql = text("""
            UPDATE document_usage_history 
            SET was_successful = :success,
                client_response = :response,
                modifications_made = :modifications,
                final_content = :final_content,
                completed_at = CURRENT_TIMESTAMP
            WHERE document_id = :doc_id 
                AND user_id = :user_id
                AND completed_at IS NULL
            ORDER BY used_at DESC
            LIMIT 1
        """)
        
        await db.execute(update_sql, {
            'success': feedback.was_successful,
            'response': feedback.client_response,
            'modifications': feedback.modifications_made,
            'final_content': feedback.final_content,
            'doc_id': feedback.document_id,
            'user_id': current_user["id"]
        })
        
        # 重新计算文书成功率
        calculate_sql = text("""
            UPDATE document_library 
            SET success_rate = (
                SELECT COALESCE(
                    (COUNT(CASE WHEN was_successful = true THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)),
                    0
                )
                FROM document_usage_history 
                WHERE document_id = :doc_id 
                AND was_successful IS NOT NULL
            )
            WHERE id = :doc_id
        """)
        
        await db.execute(calculate_sql, {'doc_id': feedback.document_id})
        await db.commit()
        
        return {
            "success": True,
            "message": "反馈提交成功，谢谢您的反馈！"
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交反馈失败: {str(e)}"
        )


@router.get("/stats")
async def get_document_library_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的文书库统计信息"""
    try:
        config_service = SystemConfigService(db)
        doc_service = DocumentLibraryService(config_service)
        
        stats = await doc_service.get_document_library_stats(db, current_user["id"])
        
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/library")
async def get_user_documents(
    document_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的文书库列表"""
    try:
        from sqlalchemy import text
        
        # 构建查询条件
        where_conditions = ["created_by = :user_id", "is_active = true"]
        params = {"user_id": current_user["id"], "limit": limit, "offset": offset}
        
        if document_type:
            where_conditions.append("document_type = :doc_type")
            params["doc_type"] = document_type
        
        query = text(f"""
            SELECT 
                id, document_type, document_title, 
                usage_count, success_rate, ai_quality_score,
                template_tags, case_keywords,
                created_at, last_used_at
            FROM document_library
            WHERE {' AND '.join(where_conditions)}
            ORDER BY usage_count DESC, success_rate DESC, created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = await db.execute(query, params)
        documents = []
        
        for row in result:
            documents.append({
                "id": str(row[0]),
                "document_type": row[1],
                "document_title": row[2],
                "usage_count": row[3],
                "success_rate": float(row[4]) if row[4] else 0,
                "quality_score": row[5],
                "template_tags": row[6] or [],
                "case_keywords": row[7] or [],
                "created_at": row[8].isoformat() if row[8] else None,
                "last_used_at": row[9].isoformat() if row[9] else None
            })
        
        # 获取总数
        count_query = text(f"""
            SELECT COUNT(*) FROM document_library
            WHERE {' AND '.join(where_conditions[:-2])}  -- 排除limit和offset相关条件
        """)
        count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
        total_result = await db.execute(count_query, count_params)
        total_count = total_result.scalar()
        
        return {
            "success": True,
            "documents": documents,
            "total_count": total_count,
            "has_more": (offset + limit) < total_count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文书库列表失败: {str(e)}"
        )


@router.get("/{document_id}")
async def get_document_detail(
    document_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取文书详细内容"""
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                id, document_type, document_title, document_content,
                usage_count, success_rate, ai_quality_score,
                template_tags, case_keywords, generation_method,
                created_at, updated_at, last_used_at
            FROM document_library
            WHERE id = :doc_id AND created_by = :user_id AND is_active = true
        """)
        
        result = await db.execute(query, {
            'doc_id': document_id,
            'user_id': current_user["id"]
        })
        
        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文书不存在或无权访问"
            )
        
        return {
            "success": True,
            "document": {
                "id": str(row[0]),
                "document_type": row[1],
                "document_title": row[2],
                "document_content": row[3],
                "usage_count": row[4],
                "success_rate": float(row[5]) if row[5] else 0,
                "quality_score": row[6],
                "template_tags": row[7] or [],
                "case_keywords": row[8] or [],
                "generation_method": row[9],
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
                "last_used_at": row[12].isoformat() if row[12] else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文书详情失败: {str(e)}"
        )