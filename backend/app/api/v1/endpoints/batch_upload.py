"""
批量上传API端点（集成Credits控制）
实现Credits检查、批量上传控制、防滥用机制
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
import logging
from datetime import datetime
import json

from app.core.deps import get_db, get_current_user
from app.services.user_credits_service import UserCreditsService, InsufficientCreditsError, create_user_credits_service
from app.services.config_service import SystemConfigService
from app.services.payment_service import create_wechat_pay_service
from app.services.batch_abuse_monitor import BatchAbuseMonitor, create_batch_abuse_monitor

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


def get_credits_service() -> UserCreditsService:
    """获取Credits服务实例"""
    config_service = SystemConfigService()
    payment_service = create_wechat_pay_service(config_service)
    return create_user_credits_service(config_service, payment_service)


def get_abuse_monitor() -> BatchAbuseMonitor:
    """获取滥用监控服务实例"""
    return create_batch_abuse_monitor()


@router.post("/batch-upload-with-credits", response_model=Dict[str, Any])
async def batch_upload_with_credits_control(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    data_type: str = Query('debt_collection', description="数据类型"),
    auto_save: bool = Query(True, description="是否自动保存"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量上传（集成Credits控制）
    
    流程：
    1. 检查Credits余额
    2. 消耗Credits
    3. 执行批量上传
    4. 记录使用情况
    """
    try:
        user_id = UUID(current_user["id"])
        credits_service = get_credits_service()
        
        # 1. 检查文件数量限制
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="请选择要上传的文件")
        
        if len(files) > 50:  # 批量上传限制
            raise HTTPException(status_code=400, detail="批量上传最多支持50个文件")
        
        # 2. 检查文件大小
        total_size = sum(file.size or 0 for file in files)
        if total_size > 500 * 1024 * 1024:  # 500MB总限制
            raise HTTPException(status_code=400, detail="批量上传总文件大小不能超过500MB")
        
        # 3. 滥用检测预检查
        abuse_monitor = get_abuse_monitor()
        abuse_patterns = await abuse_monitor.detect_abuse_patterns(user_id, db)
        
        # 如果检测到严重滥用，阻止上传
        critical_patterns = [p for p in abuse_patterns if p.severity.value in ['high', 'critical']]
        if critical_patterns:
            logger.warning(f"用户 {user_id} 批量上传被阻止，检测到严重滥用模式: {[p.pattern_type for p in critical_patterns]}")
            return {
                "success": False,
                "error": "abuse_detected",
                "message": "检测到滥用行为，批量上传已被阻止",
                "data": {
                    "abuse_patterns": [
                        {
                            "type": p.pattern_type,
                            "severity": p.severity.value,
                            "description": p.description
                        } for p in critical_patterns
                    ]
                },
                "suggestions": {
                    "contact_support": "如有疑问，请联系客服",
                    "review_guidelines": "请查看批量上传使用指南",
                    "wait_period": "建议等待24小时后再次尝试"
                }
            }
        
        # 4. Credits检查和消耗
        try:
            credits_result = await credits_service.consume_credits_for_batch_upload(user_id, db)
        except InsufficientCreditsError as e:
            return {
                "success": False,
                "error": "insufficient_credits",
                "message": e.message,
                "data": {
                    "current_credits": e.current_credits,
                    "required_credits": e.required_credits,
                    "shortage": e.required_credits - e.current_credits
                },
                "suggestions": {
                    "purchase_credits": "/api/v1/credits/purchase",
                    "wait_for_reset": "每周一自动重置1个免费Credit",
                    "single_upload": "可以使用单一任务发布（不消耗Credits）"
                },
                "pricing_info": {
                    "credit_price": 50.00,
                    "currency": "CNY",
                    "purchase_url": "/api/v1/credits/purchase"
                }
            }
        
        # 5. 创建批量上传任务记录
        batch_task_id = await create_batch_upload_task(
            user_id, files, data_type, credits_result['credits_consumed'], db
        )
        
        # 6. 记录滥用检测结果（如果有）
        if abuse_patterns:
            await abuse_monitor.record_abuse_incident(user_id, abuse_patterns, db)
        
        # 7. 执行批量处理（后台任务）
        background_tasks.add_task(
            process_batch_upload_files,
            batch_task_id, files, data_type, user_id, db
        )
        
        logger.info(f"用户 {user_id} 批量上传任务创建成功，消耗 {credits_result['credits_consumed']} Credits")
        
        return {
            "success": True,
            "message": f"批量上传任务已创建，消耗 {credits_result['credits_consumed']} Credits",
            "data": {
                "batch_task_id": batch_task_id,
                "file_count": len(files),
                "credits_consumed": credits_result['credits_consumed'],
                "credits_remaining": credits_result['credits_remaining'],
                "estimated_processing_time": f"{len(files) * 30}秒",
                "status_check_url": f"/api/v1/batch-upload/status/{batch_task_id}"
            }
        }
        
    except InsufficientCreditsError:
        # 这个异常已经在上面处理了
        raise
    except Exception as e:
        logger.error(f"批量上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.get("/check-credits", response_model=Dict[str, Any])
async def check_batch_upload_credits(
    file_count: int = Query(1, ge=1, le=50, description="文件数量"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检查批量上传Credits要求（不实际消耗）
    """
    try:
        user_id = UUID(current_user["id"])
        credits_service = get_credits_service()
        
        # 获取用户Credits信息
        credits_info = await credits_service.get_user_credits(user_id, db)
        
        required_credits = 1  # 批量上传固定消耗1个Credit
        has_sufficient = credits_info['credits_remaining'] >= required_credits
        
        return {
            "success": True,
            "data": {
                "file_count": file_count,
                "required_credits": required_credits,
                "current_credits": credits_info['credits_remaining'],
                "has_sufficient_credits": has_sufficient,
                "can_upload": has_sufficient,
                "next_reset_date": credits_info['next_reset_date'],
                "pricing_info": {
                    "credit_price": 50.00,
                    "currency": "CNY"
                }
            },
            "message": "Credits检查完成"
        }
        
    except Exception as e:
        logger.error(f"检查Credits失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查Credits失败: {str(e)}")


@router.get("/status/{batch_task_id}", response_model=Dict[str, Any])
async def get_batch_upload_status(
    batch_task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取批量上传任务状态
    """
    try:
        query = text("""
            SELECT 
                id, user_id, task_type, file_name, total_records,
                processed_records, success_records, error_records,
                credits_cost, status, error_details, created_at,
                processing_started_at, processing_completed_at
            FROM batch_upload_tasks 
            WHERE id = :task_id AND user_id = :user_id
        """)
        
        result = db.execute(query, {
            "task_id": batch_task_id,
            "user_id": current_user["id"]
        }).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="批量上传任务不存在")
        
        # 计算进度
        progress = 0
        if result[4] > 0:  # total_records
            progress = (result[5] / result[4]) * 100  # processed_records / total_records
        
        return {
            "success": True,
            "data": {
                "batch_task_id": result[0],
                "status": result[9],
                "progress": round(progress, 2),
                "total_records": result[4],
                "processed_records": result[5],
                "success_records": result[6],
                "error_records": result[7],
                "credits_cost": result[8],
                "created_at": result[11].isoformat() if result[11] else None,
                "processing_started_at": result[12].isoformat() if result[12] else None,
                "processing_completed_at": result[13].isoformat() if result[13] else None,
                "error_details": json.loads(result[10]) if result[10] else []
            }
        }
        
    except Exception as e:
        logger.error(f"获取批量上传状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/history", response_model=Dict[str, Any])
async def get_batch_upload_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="页大小"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户批量上传历史
    """
    try:
        offset = (page - 1) * size
        
        # 构建查询条件
        where_clause = "WHERE user_id = :user_id"
        params = {"user_id": current_user["id"], "size": size, "offset": offset}
        
        if status:
            where_clause += " AND status = :status"
            params["status"] = status
        
        query = text(f"""
            SELECT 
                id, task_type, file_name, total_records,
                processed_records, success_records, error_records,
                credits_cost, status, created_at, processing_completed_at
            FROM batch_upload_tasks 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :size OFFSET :offset
        """)
        
        count_query = text(f"""
            SELECT COUNT(*) FROM batch_upload_tasks {where_clause}
        """)
        
        results = db.execute(query, params).fetchall()
        total = db.execute(count_query, {k: v for k, v in params.items() if k not in ['size', 'offset']}).scalar()
        
        items = []
        for row in results:
            items.append({
                "batch_task_id": row[0],
                "task_type": row[1],
                "file_name": row[2],
                "total_records": row[3],
                "processed_records": row[4],
                "success_records": row[5],
                "error_records": row[6],
                "credits_cost": row[7],
                "status": row[8],
                "created_at": row[9].isoformat() if row[9] else None,
                "completed_at": row[10].isoformat() if row[10] else None
            })
        
        return {
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        }
        
    except Exception as e:
        logger.error(f"获取批量上传历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.post("/abuse-report", response_model=Dict[str, Any])
async def report_upload_abuse(
    batch_task_id: str,
    reason: str = Query(..., description="举报原因"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    举报滥用批量上传
    """
    try:
        # 记录举报信息（这里可以扩展为完整的举报系统）
        logger.warning(f"用户 {current_user['id']} 举报批量上传滥用: {batch_task_id}, 原因: {reason}")
        
        return {
            "success": True,
            "message": "举报已提交，我们会尽快处理"
        }
        
    except Exception as e:
        logger.error(f"提交举报失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交举报失败: {str(e)}")


async def create_batch_upload_task(
    user_id: UUID, 
    files: List[UploadFile], 
    data_type: str, 
    credits_cost: int, 
    db: Session
) -> str:
    """
    创建批量上传任务记录
    """
    try:
        import uuid
        
        batch_task_id = str(uuid.uuid4())
        file_names = [file.filename for file in files]
        total_size = sum(file.size or 0 for file in files)
        
        insert_query = text("""
            INSERT INTO batch_upload_tasks (
                id, user_id, task_type, file_name, file_size,
                total_records, processed_records, success_records, error_records,
                credits_cost, status, created_at
            ) VALUES (
                :id, :user_id, :task_type, :file_name, :file_size,
                :total_records, 0, 0, 0,
                :credits_cost, 'pending', NOW()
            )
        """)
        
        db.execute(insert_query, {
            "id": batch_task_id,
            "user_id": str(user_id),
            "task_type": data_type,
            "file_name": f"批量上传 {len(files)} 个文件: {', '.join(file_names[:3])}{'...' if len(files) > 3 else ''}",
            "file_size": total_size,
            "total_records": len(files),  # 暂时用文件数量作为记录数
            "credits_cost": credits_cost
        })
        
        db.commit()
        
        return batch_task_id
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建批量上传任务失败: {str(e)}")
        raise


async def process_batch_upload_files(
    batch_task_id: str,
    files: List[UploadFile],
    data_type: str,
    user_id: UUID,
    db: Session
):
    """
    处理批量上传文件（后台任务）
    """
    try:
        # 更新任务状态为处理中
        update_query = text("""
            UPDATE batch_upload_tasks 
            SET status = 'processing', processing_started_at = NOW()
            WHERE id = :task_id
        """)
        
        db.execute(update_query, {"task_id": batch_task_id})
        db.commit()
        
        success_count = 0
        error_count = 0
        error_details = []
        
        # 处理每个文件
        for i, file in enumerate(files):
            try:
                # 这里应该调用实际的文件处理逻辑
                # 暂时模拟处理
                await process_single_file(file, data_type)
                success_count += 1
                
                # 更新进度
                update_progress_query = text("""
                    UPDATE batch_upload_tasks 
                    SET processed_records = :processed, success_records = :success
                    WHERE id = :task_id
                """)
                
                db.execute(update_progress_query, {
                    "task_id": batch_task_id,
                    "processed": i + 1,
                    "success": success_count
                })
                db.commit()
                
            except Exception as e:
                error_count += 1
                error_details.append({
                    "file": file.filename,
                    "error": str(e)
                })
                
                logger.error(f"处理文件 {file.filename} 失败: {str(e)}")
        
        # 更新最终状态
        final_status = 'completed' if error_count == 0 else 'completed_with_errors'
        
        final_update_query = text("""
            UPDATE batch_upload_tasks 
            SET 
                status = :status,
                processed_records = :processed,
                success_records = :success,
                error_records = :errors,
                error_details = :error_details,
                processing_completed_at = NOW()
            WHERE id = :task_id
        """)
        
        db.execute(final_update_query, {
            "task_id": batch_task_id,
            "status": final_status,
            "processed": len(files),
            "success": success_count,
            "errors": error_count,
            "error_details": json.dumps(error_details)
        })
        db.commit()
        
        logger.info(f"批量上传任务 {batch_task_id} 处理完成: 成功 {success_count}, 失败 {error_count}")
        
    except Exception as e:
        # 更新任务状态为失败
        error_update_query = text("""
            UPDATE batch_upload_tasks 
            SET status = 'failed', error_details = :error
            WHERE id = :task_id
        """)
        
        db.execute(error_update_query, {
            "task_id": batch_task_id,
            "error": json.dumps([{"error": str(e)}])
        })
        db.commit()
        
        logger.error(f"批量上传任务 {batch_task_id} 处理失败: {str(e)}")


async def process_single_file(file: UploadFile, data_type: str):
    """
    处理单个文件（模拟）
    """
    # 这里应该调用实际的文件处理逻辑
    # 暂时模拟处理时间
    import asyncio
    await asyncio.sleep(1)  # 模拟处理时间
    
    # 模拟一些文件处理失败
    if "error" in file.filename.lower():
        raise Exception("文件格式错误")
    
    return {"status": "success", "records": 10}