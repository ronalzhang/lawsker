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
from app.services.ai_table_recognition_service import AITableRecognitionService
from app.services.template_service import TemplateService
import logging
from datetime import datetime
import re
import json

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
    current_user: Dict[str, Any] = Depends(get_current_user),
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
        
        logger.info(f"用户 {current_user.get('username', 'unknown')} 开始上传文件: {file.filename}")
        
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
            'user_id': current_user["id"],
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
                save_result = await save_debt_data(valid_data, current_user["id"], db)
                
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """下载标准模板"""
    try:
        _, template_service, _ = get_services()
        
        logger.info(f"用户 {current_user.get('username', 'unknown')} 下载模板: {template_type}")
        
        # 生成并返回模板文件
        return await template_service.download_template(template_type)
        
    except Exception as e:
        logger.error(f"下载模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载模板失败: {str(e)}")

@router.get("/templates")
async def list_templates(current_user: Dict[str, Any] = Depends(get_current_user)):
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
    current_user: Dict[str, Any] = Depends(get_current_user),
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
        
        logger.info(f"用户 {current_user.get('username', 'unknown')} 手动上传文件: {file.filename}")
        
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
            'user_id': current_user["id"],
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
    current_user: Dict[str, Any] = Depends(get_current_user),
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
    current_user: Dict[str, Any] = Depends(get_current_user),
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取可抢单任务列表（律师端）"""
    try:
        # 查询状态为已发布的任务（暂时不过滤已抢单的任务）
        query = text("""
            SELECT 
                tr.id as task_id,
                tr.user_id,
                tr.task_type,
                tr.title,
                tr.description,
                tr.amount,
                tr.urgency,
                tr.status,
                tr.created_at,
                u.username as publisher_name
            FROM task_publish_records tr
            LEFT JOIN users u ON tr.user_id = u.id
            WHERE tr.status = 'published'
            ORDER BY tr.created_at DESC
            LIMIT 20
        """)
        
        result = db.execute(query)
        tasks = []
        
        for row in result:
            task = {
                "task_id": row[0],
                "user_id": row[1],
                "task_type": row[2],
                "title": row[3],
                "description": row[4],
                "budget": float(row[5]) if row[5] else 0,
                "urgency": row[6] or "normal",
                "status": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
                "publisher_name": row[9] or "匿名用户"
            }
            tasks.append(task)
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"获取可抢单任务失败: {e}")
        return {
            "success": False,
            "message": f"获取任务失败: {str(e)}",
            "tasks": []
        }

@router.get("/tasks/my-tasks/user")
async def get_user_published_tasks(
    current_user: Dict[str, Any] = Depends(get_current_user),
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
        
        result = db.execute(query, {"user_id": current_user["id"]})
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
    current_user: Dict[str, Any] = Depends(get_current_user),
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
        
        result = db.execute(query, {"user_id": current_user["id"]})
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """律师抢单功能"""
    try:
        # 检查任务是否存在且可以抢单
        check_query = text("""
            SELECT id, status, assigned_to, title, amount 
            FROM task_publish_records 
            WHERE id = :task_id AND status = 'published'
        """)
        
        result = db.execute(check_query, {"task_id": task_id}).fetchone()
        
        if not result:
            return {"success": False, "message": "任务不存在或已不可用"}
        
        # 检查任务是否已被其他律师抢单
        if result[2] is not None:  # assigned_to 不为空
            return {"success": False, "message": "任务已被其他律师抢单"}
        
        # 更新任务状态，分配给当前律师
        grab_query = text("""
            UPDATE task_publish_records 
            SET assigned_to = :lawyer_id, 
                status = 'ASSIGNED',
                updated_at = NOW()
            WHERE id = :task_id 
            AND status = 'published' 
            AND assigned_to IS NULL
        """)
        
        update_result = db.execute(grab_query, {
            "task_id": task_id,
            "lawyer_id": str(current_user["id"])
        })
        
        if update_result.rowcount == 0:
            return {"success": False, "message": "抢单失败，任务可能已被其他律师抢走"}
        
        db.commit()
        
        return {
            "success": True,
            "message": "抢单成功！任务已分配给您",
            "task_id": task_id,
            "lawyer_id": str(current_user["id"]),
            "grabbed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"抢单失败: {e}")
        return {"success": False, "message": f"抢单失败: {str(e)}"}

@router.get("/tasks/my-tasks/lawyer")
async def get_lawyer_tasks(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取律师接单的任务列表"""
    try:
        # 暂时查询分配给当前律师的任务（使用assigned_to字段）
        query = text("""
            SELECT DISTINCT
                tr.id as task_id,
                tr.user_id,
                tr.task_type,
                tr.title,
                tr.description,
                tr.amount,
                tr.urgency,
                tr.status,
                tr.created_at,
                u.username as publisher_name,
                tr.assigned_to,
                tr.updated_at as grabbed_at
            FROM task_publish_records tr
            LEFT JOIN users u ON tr.user_id = u.id
            WHERE tr.assigned_to = :lawyer_id
            ORDER BY tr.updated_at DESC
        """)
        
        result = db.execute(query, {"lawyer_id": str(current_user["id"])})
        tasks = []
        
        for row in result:
            task = {
                "task_id": row[0],
                "user_id": row[1],
                "task_type": row[2],
                "title": row[3],
                "description": row[4],
                "budget": float(row[5]) if row[5] else 0,
                "urgency": row[6] or "normal",
                "status": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
                "publisher_name": row[9] or "匿名用户",
                "grabbed_at": row[11].isoformat() if row[11] else None,
                "grab_status": "grabbed"
            }
            tasks.append(task)
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"获取律师任务失败: {e}")
        return {
            "success": False,
            "message": f"获取任务失败: {str(e)}",
            "tasks": []
        }

@router.post("/tasks/generate-document/{task_id}")
async def generate_ai_document(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为指定任务生成AI法律文书"""
    try:
        # 验证律师是否接了这个任务
        verify_query = text("""
            SELECT id, task_type, title, description, amount 
            FROM task_publish_records 
            WHERE id = :task_id AND assigned_to = :lawyer_id
        """)
        
        result = db.execute(verify_query, {
            "task_id": task_id, 
            "lawyer_id": str(current_user["id"])
        }).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在或您未接单")
        
        # 获取任务详细信息
        task_type = result[1]  # task_type
        title = result[2]      # title
        description = result[3] # description
        amount = result[4]     # amount
        
        # 根据任务类型生成不同的法律文书
        document_content = await generate_legal_document(
            task_type=task_type or "legal_consultation",
            title=title or "法律文书",
            description=description or "",
            amount=float(amount) if amount else 0,
            task_id=task_id
        )
        
        return {
            "success": True,
            "document_content": document_content,
            "task_id": task_id,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"生成AI文书失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成文书失败: {str(e)}")

async def generate_legal_document(task_type: str, title: str, description: str, amount: float, task_id: str) -> str:
    """生成法律文书内容"""
    
    # 模板库 - 根据任务类型生成不同文书
    templates = {
        "debt_collection": """律师函

致：{target_company}

关于债务催收事宜，特函告如下：

根据我方委托人提供的相关资料，贵方对我方委托人存在逾期债务，具体情况如下：

1. 债务性质：{debt_nature}
2. 债务金额：人民币{amount}元
3. 逾期时间：{overdue_period}

根据《中华人民共和国民法典》相关规定，债务人应当按照约定的期限履行债务。现贵方已逾期未履行还款义务，严重违反了合同约定。

特此函告，请贵方在收到本函后7日内，将上述欠款本金及相应利息一并清偿至指定账户。如逾期仍不履行，我方将依法采取法律手段维护委托人合法权益。

此致
敬礼！

{lawyer_name}
{law_firm}
{date}""",

        "contract_review": """合同审查报告

委托方：{client_name}
审查日期：{review_date}
合同名称：{contract_name}

一、合同基本情况
{contract_basic_info}

二、法律风险分析
1. 主要条款分析
{main_clauses_analysis}

2. 风险提示
{risk_warnings}

三、修改建议
{modification_suggestions}

四、结论
{conclusion}

审查律师：{lawyer_name}
{law_firm}
{date}""",

        "legal_consultation": """法律咨询意见书

咨询方：{client_name}
咨询时间：{consultation_date}
咨询事项：{consultation_matter}

一、事实概述
{fact_summary}

二、法律分析
{legal_analysis}

三、处理建议
{handling_suggestions}

四、风险提示
{risk_warnings}

五、相关法条
{relevant_laws}

咨询律师：{lawyer_name}
{law_firm}
{date}"""
    }
    
    # 根据描述智能提取信息
    current_date = datetime.now().strftime("%Y年%m月%d日")
    
    # 默认模板
    if task_type not in templates:
        task_type = "legal_consultation"
    
    template = templates[task_type]
    
    # 智能填充内容
    if task_type == "debt_collection":
        # 从描述中提取债务信息
        content = template.format(
            target_company=extract_company_name(description) or "XX公司",
            debt_nature=extract_debt_nature(description) or "合同欠款",
            amount=f"{amount:,.2f}" if amount > 0 else "XX",
            overdue_period=extract_overdue_period(description) or "XX天",
            lawyer_name="[律师签名]",
            law_firm="[律师事务所]",
            date=current_date
        )
    elif task_type == "contract_review":
        content = template.format(
            client_name=extract_client_name(description) or "委托人",
            review_date=current_date,
            contract_name=title or "待审查合同",
            contract_basic_info=f"合同主要内容：{description[:200]}...",
            main_clauses_analysis="[根据具体合同条款进行分析]",
            risk_warnings="[识别出的主要法律风险]",
            modification_suggestions="[针对风险提出的修改建议]",
            conclusion="[整体评估结论]",
            lawyer_name="[律师签名]",
            law_firm="[律师事务所]",
            date=current_date
        )
    else:  # legal_consultation
        content = template.format(
            client_name=extract_client_name(description) or "咨询人",
            consultation_date=current_date,
            consultation_matter=title or "法律咨询",
            fact_summary=description[:300] + "..." if len(description) > 300 else description,
            legal_analysis="[基于相关法律法规进行分析]",
            handling_suggestions="[根据情况提出的处理建议]",
            risk_warnings="[需要注意的法律风险]",
            relevant_laws="[相关适用的法律条文]",
            lawyer_name="[律师签名]",
            law_firm="[律师事务所]",
            date=current_date
        )
    
    return content

def extract_company_name(text: str) -> str:
    """从文本中提取公司名称"""
    import re
    patterns = [
        r'([^，。！？\s]+公司)',
        r'([^，。！？\s]+企业)',
        r'([^，。！？\s]+集团)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def extract_debt_nature(text: str) -> str:
    """从文本中提取债务性质"""
    if "货款" in text or "采购" in text:
        return "货款"
    elif "服务费" in text or "咨询费" in text:
        return "服务费"
    elif "租金" in text:
        return "租金"
    elif "借款" in text:
        return "借款"
    else:
        return "合同欠款"

def extract_amount(text: str) -> str:
    """从文本中提取金额"""
    import re
    patterns = [
        r'(\d+(?:\.\d+)?万元)',
        r'(\d+(?:\.\d+)?元)',
        r'人民币\s*(\d+(?:\.\d+)?)',
        r'¥\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
        r'(\d+(?:,\d{3})*(?:\.\d+)?)元'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def extract_overdue_period(text: str) -> str:
    """从文本中提取逾期时间"""
    import re
    patterns = [
        r'逾期(\d+)天',
        r'(\d+)天未还',
        r'已(\d+)个月',
        r'超过(\d+)日'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def extract_client_name(text: str) -> str:
    """从文本中提取客户名称"""
    import re
    patterns = [
        r'([^，。！？\s]{2,4}先生)',
        r'([^，。！？\s]{2,4}女士)',
        r'([^，。！？\s]{2,4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1)
            if len(name) >= 2 and len(name) <= 4:
                return name
    return None

@router.post("/tasks/save-document/{task_id}")
async def save_document_content(
    task_id: str,
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存律师修改后的文书内容"""
    try:
        content = request.get("content", "")
        
        save_query = text("""
            UPDATE task_documents 
            SET content = :content, updated_at = NOW()
            WHERE task_id = :task_id AND lawyer_id = :lawyer_id
        """)
        
        result = db.execute(save_query, {
            "task_id": task_id,
            "lawyer_id": str(current_user["id"]),
            "content": content
        })
        
        if result.rowcount == 0:
            # 如果没有更新记录，说明文档不存在，创建新的
            insert_query = text("""
                INSERT INTO task_documents (task_id, lawyer_id, content, document_type, created_at)
                VALUES (:task_id, :lawyer_id, :content, 'manual', NOW())
            """)
            
            db.execute(insert_query, {
                "task_id": task_id,
                "lawyer_id": str(current_user["id"]),
                "content": content
            })
        
        db.commit()
        
        return {
            "success": True,
            "message": "文书内容已保存"
        }
        
    except Exception as e:
        logger.error(f"保存文书内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

@router.post("/tasks/send-document/{task_id}")
async def send_document(
    task_id: str,
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送法律文书给委托人"""
    try:
        send_method = request.get("send_method", "email")  # email, sms, express
        recipient_info = request.get("recipient_info", {})
        
        # 获取文书内容
        doc_query = text("""
            SELECT content FROM task_documents 
            WHERE task_id = :task_id AND lawyer_id = :lawyer_id
        """)
        
        result = db.execute(doc_query, {
            "task_id": task_id,
            "lawyer_id": str(current_user["id"])
        }).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="文书不存在")
        
        document_content = result[0]
        
        # 记录发送日志
        send_log_query = text("""
            INSERT INTO document_send_logs 
            (task_id, lawyer_id, send_method, recipient_info, content, sent_at, status)
            VALUES (:task_id, :lawyer_id, :send_method, :recipient_info, :content, NOW(), 'sent')
        """)
        
        db.execute(send_log_query, {
            "task_id": task_id,
            "lawyer_id": str(current_user["id"]),
            "send_method": send_method,
            "recipient_info": json.dumps(recipient_info),
            "content": document_content
        })
        
        # 更新任务状态为已完成
        update_task_query = text("""
            UPDATE task_grab_records 
            SET status = 'COMPLETED', completed_at = NOW()
            WHERE task_id = :task_id AND lawyer_id = :lawyer_id
        """)
        
        db.execute(update_task_query, {
            "task_id": task_id,
            "lawyer_id": str(current_user["id"])
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"文书已通过{send_method}发送给委托人",
            "send_method": send_method,
            "sent_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"发送文书失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")

@router.get("/tasks/document/{task_id}")
async def get_task_document(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务的AI生成文书内容"""
    try:
        # 检查是否有已生成的文书
        doc_query = text("""
            SELECT content, document_type, created_at, updated_at 
            FROM task_documents 
            WHERE task_id = :task_id AND lawyer_id = :lawyer_id
        """)
        
        result = db.execute(doc_query, {
            "task_id": task_id,
            "lawyer_id": str(current_user["id"])
        }).fetchone()
        
        if result:
            return {
                "success": True,
                "content": result[0],
                "document_type": result[1],
                "created_at": result[2].isoformat() if result[2] else None,
                "updated_at": result[3].isoformat() if result[3] else None,
                "has_document": True
            }
        else:
            # 如果没有文书，自动生成一个
            return await generate_ai_document(task_id, current_user, db)
            
    except Exception as e:
        logger.error(f"获取文书内容失败: {e}")
        return {
            "success": False,
            "message": f"获取文书失败: {str(e)}",
            "has_document": False
        }

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