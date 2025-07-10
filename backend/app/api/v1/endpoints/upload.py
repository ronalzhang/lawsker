"""
文件上传API端点
支持AI智能表格识别、标准模板下载、数据验证等功能
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.ai_table_recognition_service import AITableRecognitionService
from app.services.template_service import TemplateService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# 初始化服务
ai_recognition_service = None
template_service = TemplateService()

def get_services():
    """获取服务实例"""
    global ai_recognition_service
    
    if ai_recognition_service is None:
        ai_recognition_service = AITableRecognitionService()
    
    return ai_recognition_service, template_service

@router.post("/smart-upload", response_model=Dict[str, Any])
async def smart_table_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    data_type: str = Query('debt_collection', description="数据类型"),
    auto_save: bool = Query(True, description="是否自动保存成功识别的数据"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    智能表格上传和识别
    
    流程：
    1. 上传文件 → 2. AI识别 → 3. 数据验证 → 4. 自动保存（可选）
    
    如果AI识别失败，返回标准模板下载链接
    """
    try:
        # 获取服务实例
        ai_service, template_service = get_services()
        
        # 验证文件
        if not file.filename:
            raise HTTPException(status_code=400, detail="请选择要上传的文件")
        
        if file.size and file.size > 50 * 1024 * 1024:  # 50MB限制
            raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
        
        logger.info(f"用户 {current_user.username} 开始上传文件: {file.filename}")
        
        # AI智能识别
        recognition_result = await ai_service.recognize_and_convert_table(file, data_type)
        
        if not recognition_result['success']:
            # AI识别失败，返回错误和模板下载建议
            return {
                'success': False,
                'step': 'ai_recognition',
                'error': recognition_result['error'],
                'suggestion': recognition_result.get('suggestion', '建议下载标准模板重新填写'),
                'template_info': template_service.get_template_info(data_type),
                'fallback_options': {
                    'download_template': f'/api/v1/upload/template/download?type={data_type}',
                    'manual_upload': '/api/v1/upload/manual',
                    'help_guide': '/help/upload-guide'
                }
            }
        
        # AI识别成功，处理数据
        converted_data = recognition_result['converted_data']
        validation_result = recognition_result['validation_result']
        
        response_data = {
            'success': True,
            'step': 'ai_recognition_success',
            'message': f'AI成功识别并转换 {len(converted_data)} 条记录',
            'user_id': current_user.id,
            'original_filename': file.filename,
            'recognition_result': {
                'total_records': len(converted_data),
                'valid_records': validation_result['valid_count'],
                'invalid_records': validation_result['invalid_count'],
                'success_rate': f"{validation_result['valid_count']/len(converted_data)*100:.1f}%",
                'ai_confidence': recognition_result.get('ai_confidence', 0),
                'field_mapping': recognition_result['field_mapping']
            },
            'data_preview': converted_data[:5],  # 显示前5条数据
            'validation_summary': {
                'errors': validation_result['errors'][:10],  # 显示前10个错误
                'warnings': validation_result['warnings'][:10]
            },
            'next_steps': []
        }
        
        # 如果有无效数据，提供建议
        if validation_result['invalid_count'] > 0:
            response_data['next_steps'].append({
                'action': 'review_errors',
                'message': f'发现 {validation_result["invalid_count"]} 条无效记录，请检查数据',
                'url': '/api/v1/upload/review-errors'
            })
        
        # 自动保存有效数据
        if auto_save and validation_result['valid_count'] > 0:
            try:
                # 过滤出有效数据
                valid_data = []
                error_rows = set(error['row'] for error in validation_result['errors'])
                
                for i, row in enumerate(converted_data):
                    if (i + 1) not in error_rows:
                        valid_data.append(row)
                
                # 保存到数据库（这里需要根据实际的数据保存服务来实现）
                save_result = await save_debt_data(valid_data, current_user.id, db)
                
                response_data['auto_save_result'] = {
                    'saved_count': len(valid_data),
                    'save_id': save_result.get('batch_id'),
                    'message': f'已自动保存 {len(valid_data)} 条有效数据'
                }
                
                response_data['next_steps'].append({
                    'action': 'view_saved_data',
                    'message': '查看已保存的数据',
                    'url': f'/api/v1/data/debt-collection/batch/{save_result.get("batch_id")}'
                })
                
            except Exception as e:
                logger.error(f"自动保存数据失败: {str(e)}")
                response_data['auto_save_result'] = {
                    'error': f'自动保存失败: {str(e)}',
                    'message': '请手动确认保存数据'
                }
        
        # 添加后续操作选项
        response_data['next_steps'].extend([
            {
                'action': 'download_processed',
                'message': '下载处理后的数据',
                'url': '/api/v1/upload/download-processed'
            },
            {
                'action': 'upload_more',
                'message': '继续上传更多文件',
                'url': '/api/v1/upload/smart-upload'
            }
        ])
        
        return response_data
        
    except Exception as e:
        logger.error(f"智能上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传处理失败: {str(e)}")

@router.get("/template/info")
async def get_template_info(
    template_type: str = Query('debt_collection', description="模板类型"),
    current_user: User = Depends(get_current_user)
):
    """获取模板信息"""
    try:
        _, template_service, _ = get_services()
        template_info = template_service.get_template_info(template_type)
        
        return {
            'success': True,
            'template_info': template_info,
            'download_url': f'/api/v1/upload/template/download?type={template_type}'
        }
        
    except Exception as e:
        logger.error(f"获取模板信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板信息失败: {str(e)}")

@router.get("/template/download")
async def download_template(
    template_type: str = Query('debt_collection', description="模板类型"),
    current_user: User = Depends(get_current_user)
):
    """下载标准模板"""
    try:
        _, template_service, _ = get_services()
        
        logger.info(f"用户 {current_user.username} 下载模板: {template_type}")
        
        # 生成并返回模板文件
        return await template_service.download_template(template_type)
        
    except Exception as e:
        logger.error(f"下载模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载模板失败: {str(e)}")

@router.get("/templates")
async def list_templates(current_user: User = Depends(get_current_user)):
    """获取所有可用模板列表"""
    try:
        _, template_service, _ = get_services()
        templates = template_service.get_available_templates()
        
        return {
            'success': True,
            'templates': templates,
            'total_count': len(templates)
        }
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")

@router.post("/manual", response_model=Dict[str, Any])
async def manual_upload(
    file: UploadFile = File(...),
    data_type: str = Query('debt_collection', description="数据类型"),
    skip_validation: bool = Query(False, description="跳过数据验证"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    传统文件上传（不使用AI识别）
    要求用户上传的文件必须严格按照标准模板格式
    """
    try:
        # 这里实现传统的文件上传逻辑
        # 直接按标准格式解析，不进行AI识别
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="请选择要上传的文件")
        
        logger.info(f"用户 {current_user.username} 手动上传文件: {file.filename}")
        
        # 解析标准格式文件
        parsed_result = await parse_standard_format_file(file, data_type)
        
        if not parsed_result['success']:
            return {
                'success': False,
                'error': parsed_result['error'],
                'suggestion': '请确保文件严格按照标准模板格式填写',
                'template_download': f'/api/v1/upload/template/download?type={data_type}'
            }
        
        # 数据验证
        if not skip_validation:
            validation_result = await validate_data(parsed_result['data'], data_type)
        else:
            validation_result = {'valid_count': len(parsed_result['data']), 'invalid_count': 0}
        
        return {
            'success': True,
            'message': f'成功解析 {len(parsed_result["data"])} 条记录',
            'user_id': current_user.id,
            'filename': file.filename,
            'total_records': len(parsed_result['data']),
            'valid_records': validation_result['valid_count'],
            'invalid_records': validation_result['invalid_count'],
            'data_preview': parsed_result['data'][:5]
        }
        
    except Exception as e:
        logger.error(f"手动上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/status/{upload_id}")
async def get_upload_status(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取上传任务状态"""
    try:
        # 这里实现上传状态查询逻辑
        # 可以查询数据库中的上传任务状态
        
        return {
            'success': True,
            'upload_id': upload_id,
            'status': 'completed',  # pending, processing, completed, failed
            'progress': 100,
            'message': '上传完成'
        }
        
    except Exception as e:
        logger.error(f"获取上传状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.post("/batch-process")
async def batch_process_files(
    files: List[UploadFile] = File(...),
    data_type: str = Query('debt_collection'),
    processing_mode: str = Query('smart', description="处理模式: smart(AI识别) 或 manual(标准格式)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量文件处理"""
    try:
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="单次最多上传10个文件")
        
        results = []
        
        for file in files:
            try:
                if processing_mode == 'smart':
                    result = await smart_table_upload(
                        BackgroundTasks(), file, data_type, False, current_user, db
                    )
                else:
                    result = await manual_upload(file, data_type, False, current_user, db)
                
                results.append({
                    'filename': file.filename,
                    'result': result
                })
                
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'message': f'批量处理完成，共处理 {len(files)} 个文件',
            'results': results,
            'summary': {
                'total_files': len(files),
                'success_count': len([r for r in results if 'error' not in r]),
                'failed_count': len([r for r in results if 'error' in r])
            }
        }
        
    except Exception as e:
        logger.error(f"批量处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")

@router.get("/tasks/available")
async def get_available_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取可抢单任务列表（律师端）"""
    try:
        # 查询状态为已发布且未被抢单的任务
        query = text("""
            SELECT 
                tr.task_id,
                tr.user_id,
                tr.task_type,
                tr.title,
                tr.description,
                tr.budget,
                tr.deadline,
                tr.status,
                tr.created_at,
                u.username as publisher_name
            FROM task_publish_records tr
            LEFT JOIN users u ON tr.user_id = u.id
            WHERE tr.status = 'published'
            AND tr.task_id NOT IN (
                SELECT DISTINCT task_id 
                FROM task_grab_records 
                WHERE status IN ('grabbed', 'completed')
            )
            ORDER BY tr.created_at DESC
            LIMIT 20
        """)
        
        result = db.execute(query)
        tasks = []
        
        for row in result:
            task_data = {
                "task_id": row.task_id,
                "user_id": str(row.user_id),
                "task_type": row.task_type,
                "title": row.title,
                "description": row.description,
                "budget": float(row.budget) if row.budget else None,
                "deadline": row.deadline.isoformat() if row.deadline else None,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
                "publisher_name": row.publisher_name
            }
            tasks.append(task_data)
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"获取可抢单任务失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取任务列表失败: {str(e)}",
            "tasks": []
        }

@router.get("/tasks/my-tasks/user")
async def get_user_published_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户发布的任务列表"""
    try:
        # 查询当前用户发布的所有任务
        query = text("""
            SELECT 
                tr.task_id,
                tr.task_type,
                tr.title,
                tr.description,
                tr.budget,
                tr.deadline,
                tr.status,
                tr.created_at,
                tr.updated_at,
                tgr.lawyer_id,
                l.username as lawyer_name,
                tgr.grabbed_at
            FROM task_publish_records tr
            LEFT JOIN task_grab_records tgr ON tr.task_id = tgr.task_id AND tgr.status != 'cancelled'
            LEFT JOIN users l ON tgr.lawyer_id = l.id
            WHERE tr.user_id = :user_id
            ORDER BY tr.created_at DESC
        """)
        
        result = db.execute(query, {"user_id": current_user.id})
        tasks = []
        
        for row in result:
            task_data = {
                "task_id": row.task_id,
                "task_type": row.task_type,
                "title": row.title,
                "description": row.description,
                "budget": float(row.budget) if row.budget else None,
                "deadline": row.deadline.isoformat() if row.deadline else None,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "lawyer_id": str(row.lawyer_id) if row.lawyer_id else None,
                "lawyer_name": row.lawyer_name,
                "grabbed_at": row.grabbed_at.isoformat() if row.grabbed_at else None
            }
            tasks.append(task_data)
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"获取用户任务失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取任务列表失败: {str(e)}",
            "tasks": []
        }

@router.get("/tasks/feedback")
async def get_task_feedback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户任务的反馈状态（已被律师接单的任务）"""
    try:
        # 查询当前用户已被律师接单的任务反馈
        query = text("""
            SELECT 
                tr.task_id,
                tr.title,
                tr.task_type,
                tr.budget,
                tr.created_at,
                tgr.lawyer_id,
                l.username as lawyer_name,
                tgr.grabbed_at,
                tgr.status as grab_status,
                tgr.lawyer_message,
                tgr.contact_exchanged,
                tgr.completed_at
            FROM task_publish_records tr
            INNER JOIN task_grab_records tgr ON tr.task_id = tgr.task_id
            INNER JOIN users l ON tgr.lawyer_id = l.id
            WHERE tr.user_id = :user_id
            AND tgr.status IN ('grabbed', 'contact_exchanged', 'completed')
            ORDER BY tgr.grabbed_at DESC
        """)
        
        result = db.execute(query, {"user_id": current_user.id})
        tasks = []
        
        for row in result:
            task_data = {
                "id": row.task_id,
                "task_id": row.task_id,
                "title": row.title,
                "task_type": row.task_type,
                "budget": float(row.budget) if row.budget else None,
                "created_at": row.created_at.isoformat(),
                "lawyer_id": str(row.lawyer_id),
                "lawyer_name": row.lawyer_name,
                "accepted_at": row.grabbed_at.isoformat(),
                "status": row.grab_status,
                "lawyer_message": row.lawyer_message,
                "contact_exchanged": bool(row.contact_exchanged),
                "completed_at": row.completed_at.isoformat() if row.completed_at else None
            }
            tasks.append(task_data)
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"获取任务反馈失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取任务反馈失败: {str(e)}",
            "tasks": []
        }

@router.post("/tasks/grab/{task_id}")
async def grab_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """律师抢单功能"""
    try:
        # 检查任务是否存在且可抢单
        task_query = text("""
            SELECT task_id, user_id, title, budget, status 
            FROM task_publish_records 
            WHERE task_id = :task_id AND status = 'published'
        """)
        task_result = db.execute(task_query, {"task_id": task_id}).fetchone()
        
        if not task_result:
            return {"success": False, "message": "任务不存在或已被抢单"}
        
        # 检查是否已被其他律师抢单
        grab_check = text("""
            SELECT lawyer_id FROM task_grab_records 
            WHERE task_id = :task_id AND status IN ('grabbed', 'completed')
        """)
        existing_grab = db.execute(grab_check, {"task_id": task_id}).fetchone()
        
        if existing_grab:
            return {"success": False, "message": "任务已被其他律师抢单"}
        
        # 创建抢单记录
        grab_insert = text("""
            INSERT INTO task_grab_records (
                task_id, lawyer_id, grabbed_at, status, lawyer_message
            ) VALUES (
                :task_id, :lawyer_id, NOW(), 'grabbed', '律师已接单，正在准备处理您的案件'
            )
        """)
        db.execute(grab_insert, {
            "task_id": task_id,
            "lawyer_id": current_user.id
        })
        
        # 更新任务状态
        update_task = text("""
            UPDATE task_publish_records 
            SET status = 'grabbed', updated_at = NOW()
            WHERE task_id = :task_id
        """)
        db.execute(update_task, {"task_id": task_id})
        
        db.commit()
        
        return {
            "success": True,
            "message": "抢单成功！任务已添加到您的工作台",
            "task_id": task_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"抢单失败: {str(e)}")
        return {"success": False, "message": f"抢单失败: {str(e)}"}

# 辅助函数

async def save_debt_data(data: List[Dict[str, Any]], user_id: int, db: Session) -> Dict[str, Any]:
    """保存债务催收数据到数据库"""
    try:
        # 这里实现实际的数据保存逻辑
        # 需要根据你的数据模型来实现
        
        import uuid
        batch_id = str(uuid.uuid4())
        
        # 模拟保存过程
        logger.info(f"保存 {len(data)} 条债务数据，批次ID: {batch_id}")
        
        return {
            'batch_id': batch_id,
            'saved_count': len(data),
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"保存数据失败: {str(e)}")
        raise Exception(f"保存数据失败: {str(e)}")

async def parse_standard_format_file(file: UploadFile, data_type: str) -> Dict[str, Any]:
    """解析标准格式文件"""
    try:
        # 这里实现标准格式文件解析
        # 直接按照预定义的格式解析，不使用AI
        
        ai_service, _, _ = get_services()
        
        # 重置文件指针
        await file.seek(0)
        
        # 使用AI服务的基础解析功能（不进行智能映射）
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            content = await file.read()
            raw_data = await ai_service._parse_excel_data(content)
        elif file.filename.endswith('.csv'):
            content = await file.read()
            raw_data = await ai_service._parse_csv_data(content)
        else:
            return {'success': False, 'error': '不支持的文件格式'}
        
        if not raw_data:
            return {'success': False, 'error': '文件内容为空'}
        
        # 验证是否符合标准格式（字段名匹配）
        expected_fields = ai_service.standard_fields.keys()
        actual_fields = set(raw_data[0].keys()) if raw_data else set()
        
        # 检查必填字段是否存在
        missing_required = []
        for field in ai_service.required_fields:
            field_names = ai_service.standard_fields[field]
            if not any(name in actual_fields for name in field_names):
                missing_required.append(field)
        
        if missing_required:
            return {
                'success': False,
                'error': f'缺少必填字段: {missing_required}',
                'expected_fields': list(expected_fields),
                'actual_fields': list(actual_fields)
            }
        
        return {
            'success': True,
            'data': raw_data,
            'field_count': len(actual_fields),
            'record_count': len(raw_data)
        }
        
    except Exception as e:
        logger.error(f"解析标准格式文件失败: {str(e)}")
        return {'success': False, 'error': f'文件解析失败: {str(e)}'}

async def validate_data(data: List[Dict[str, Any]], data_type: str) -> Dict[str, Any]:
    """验证数据"""
    try:
        ai_service, _, _ = get_services()
        
        # 转换为标准格式后验证
        converted_data = await ai_service._convert_to_standard_format(data, {})
        validation_result = await ai_service._validate_converted_data(converted_data)
        
        return validation_result
        
    except Exception as e:
        logger.error(f"数据验证失败: {str(e)}")
        return {
            'valid_count': 0,
            'invalid_count': len(data),
            'errors': [{'error': f'验证失败: {str(e)}'}],
            'warnings': []
        } 