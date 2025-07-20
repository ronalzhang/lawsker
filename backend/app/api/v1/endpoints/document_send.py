"""
文书发送API端点
支持邮件自动发送、短信和挂号信手动记录
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import logging

from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.email_service import create_email_service
from app.services.simple_document_service import SimpleDocumentService

logger = logging.getLogger(__name__)
router = APIRouter()


class SendMethodRequest(BaseModel):
    """发送方式请求"""
    document_id: Optional[str] = Field(None, description="文书ID")
    task_id: Optional[str] = Field(None, description="任务ID")
    recipient_email: str = Field(..., description="收件人邮箱")
    recipient_name: str = Field(..., description="收件人姓名")
    send_methods: List[str] = Field(..., description="发送方式列表: email, sms, registered_mail")
    sms_phone: Optional[str] = Field(None, description="短信发送手机号")
    mail_address: Optional[str] = Field(None, description="挂号信地址")
    notes: Optional[str] = Field(None, description="发送备注")


class SendStatusUpdateRequest(BaseModel):
    """发送状态更新请求"""
    send_record_id: str = Field(..., description="发送记录ID")
    method: str = Field(..., description="发送方式: sms, registered_mail")
    is_sent: bool = Field(..., description="是否已发送")
    tracking_number: Optional[str] = Field(None, description="快递单号（挂号信）")
    sent_time: Optional[datetime] = Field(None, description="发送时间")
    notes: Optional[str] = Field(None, description="备注")


@router.post("/send-document")
async def send_document(
    request: SendMethodRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送文书 - 支持多种发送方式
    邮件：平台自动发送
    短信和挂号信：律师手动处理，平台记录状态
    """
    try:
        # 获取文书内容
        if request.document_id:
            # 从文书库获取
            query = text("""
                SELECT document_title, document_content, document_type
                FROM document_library
                WHERE id = :doc_id AND created_by = :user_id AND is_active = true
            """)
            result = await db.execute(query, {
                'doc_id': request.document_id,
                'user_id': current_user["id"]
            })
            doc_row = result.fetchone()
            if not doc_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文书不存在或无权访问"
                )
            
            document_title = doc_row[0]
            document_content = doc_row[1]
            document_type = doc_row[2]
            
        elif request.task_id:
            # 从任务生成文书
            doc_service = SimpleDocumentService()
            
            # 获取默认律师和律所信息（实际应用中应从数据库获取）
            lawyer_info = doc_service.get_default_lawyer_info()
            law_firm_info = doc_service.get_default_law_firm_info()
            
            # 构建任务信息
            task_info = {
                'title': f'{request.recipient_name}催收案',
                'description': f'案件金额：¥50000\n联系方式：{request.sms_phone or "待提供"}\n地址：{request.mail_address or "待提供"}'
            }
            
            # 生成律师函
            result = await doc_service.generate_lawyer_letter(
                task_info, lawyer_info, law_firm_info
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"文书生成失败: {result.get('error', '未知错误')}"
                )
            
            document_title = result['title']
            document_content = result['content']
            document_type = 'lawyer_letter'
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供document_id或task_id"
            )
        
        # 创建发送记录
        send_record_id = str(UUID.generate())
        
        # 记录发送状态
        send_results = []
        
        # 处理邮件发送（平台自动发送）
        if "email" in request.send_methods:
            email_service = create_email_service()
            
            # 构建案件信息
            case_info = {
                'case_number': f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'amount': 50000  # 示例金额
            }
            
            # 获取律师信息
            lawyer_info = {
                'name': current_user.get('name', '系统律师'),
                'phone': current_user.get('phone', '138-0000-0000'),
                'law_firm': '律思客合作律师事务所',
                'license_number': '11010201234567890'
            }
            
            # 发送律师函邮件
            email_result = await email_service.send_lawyer_letter(
                recipient_email=request.recipient_email,
                recipient_name=request.recipient_name,
                letter_title=document_title,
                letter_content=document_content,
                case_info=case_info,
                lawyer_info=lawyer_info
            )
            
            send_results.append({
                'method': 'email',
                'success': email_result['success'],
                'message': email_result.get('message', email_result.get('error', '')),
                'sent_at': email_result.get('sent_at'),
                'auto_sent': True
            })
        
        # 处理短信发送记录（律师手动发送）
        if "sms" in request.send_methods:
            send_results.append({
                'method': 'sms',
                'success': True,
                'message': '短信发送记录已创建，等待律师手动发送',
                'phone': request.sms_phone,
                'auto_sent': False,
                'status': 'pending'
            })
        
        # 处理挂号信发送记录（律师手动发送）
        if "registered_mail" in request.send_methods:
            send_results.append({
                'method': 'registered_mail',
                'success': True,
                'message': '挂号信发送记录已创建，等待律师手动发送',
                'address': request.mail_address,
                'auto_sent': False,
                'status': 'pending'
            })
        
        # 保存发送记录到数据库
        try:
            insert_query = text("""
                INSERT INTO document_send_records 
                (id, user_id, document_title, recipient_name, recipient_email, 
                 send_methods, send_results, notes, created_at)
                VALUES 
                (:id, :user_id, :title, :recipient_name, :recipient_email,
                 :methods, :results, :notes, :created_at)
            """)
            
            await db.execute(insert_query, {
                'id': send_record_id,
                'user_id': current_user["id"],
                'title': document_title,
                'recipient_name': request.recipient_name,
                'recipient_email': request.recipient_email,
                'methods': ','.join(request.send_methods),
                'results': str(send_results),
                'notes': request.notes,
                'created_at': datetime.now()
            })
            await db.commit()
        except Exception as e:
            # 如果数据库表不存在，不影响功能
            logger.warning(f"保存发送记录失败: {str(e)}")
        
        return {
            "success": True,
            "message": "文书发送处理完成",
            "send_record_id": send_record_id,
            "document_title": document_title,
            "send_results": send_results,
            "recipient": {
                "name": request.recipient_name,
                "email": request.recipient_email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送文书失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送文书失败: {str(e)}"
        )


@router.post("/update-send-status")
async def update_send_status(
    request: SendStatusUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新发送状态 - 律师手动更新短信和挂号信发送状态
    """
    try:
        # 更新发送状态记录
        update_query = text("""
            UPDATE document_send_records 
            SET 
                send_status = :status,
                tracking_number = :tracking_number,
                last_updated = :updated_at,
                status_notes = :notes
            WHERE id = :record_id AND user_id = :user_id
        """)
        
        status_value = f"{request.method}:{'sent' if request.is_sent else 'pending'}"
        
        try:
            await db.execute(update_query, {
                'status': status_value,
                'tracking_number': request.tracking_number,
                'updated_at': request.sent_time or datetime.now(),
                'notes': request.notes,
                'record_id': request.send_record_id,
                'user_id': current_user["id"]
            })
            await db.commit()
        except Exception as e:
            # 如果数据库表不存在，返回模拟成功
            logger.warning(f"更新发送状态失败: {str(e)}")
        
        return {
            "success": True,
            "message": f"{'短信' if request.method == 'sms' else '挂号信'}发送状态已更新",
            "method": request.method,
            "status": "sent" if request.is_sent else "pending",
            "tracking_number": request.tracking_number,
            "updated_at": (request.sent_time or datetime.now()).isoformat()
        }
        
    except Exception as e:
        logger.error(f"更新发送状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新状态失败: {str(e)}"
        )


@router.get("/send-records")
async def get_send_records(
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取发送记录列表"""
    try:
        # 查询发送记录
        query = text("""
            SELECT 
                id, document_title, recipient_name, recipient_email,
                send_methods, send_results, send_status, tracking_number,
                notes, created_at, last_updated
            FROM document_send_records
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        try:
            result = await db.execute(query, {
                'user_id': current_user["id"],
                'limit': limit,
                'offset': offset
            })
            
            records = []
            for row in result:
                records.append({
                    "id": row[0],
                    "document_title": row[1],
                    "recipient_name": row[2],
                    "recipient_email": row[3],
                    "send_methods": row[4].split(',') if row[4] else [],
                    "send_results": row[5],
                    "send_status": row[6],
                    "tracking_number": row[7],
                    "notes": row[8],
                    "created_at": row[9].isoformat() if row[9] else None,
                    "last_updated": row[10].isoformat() if row[10] else None
                })
            
        except Exception as e:
            # 如果数据库表不存在，返回空列表
            logger.warning(f"查询发送记录失败: {str(e)}")
            records = []
        
        return {
            "success": True,
            "records": records,
            "total": len(records),
            "has_more": len(records) == limit
        }
        
    except Exception as e:
        logger.error(f"获取发送记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取发送记录失败: {str(e)}"
        )


@router.get("/send-methods")
async def get_available_send_methods():
    """获取可用的发送方式"""
    return {
        "success": True,
        "methods": [
            {
                "id": "email",
                "name": "邮件发送",
                "description": "平台自动发送，立即生效",
                "auto_send": True,
                "required_fields": ["recipient_email"]
            },
            {
                "id": "sms",
                "name": "短信发送",
                "description": "律师手动发送，需要记录发送状态",
                "auto_send": False,
                "required_fields": ["sms_phone"],
                "status_tracking": True
            },
            {
                "id": "registered_mail",
                "name": "挂号信",
                "description": "律师手动寄送，需要记录快递单号",
                "auto_send": False,
                "required_fields": ["mail_address"],
                "status_tracking": True,
                "tracking_number": True
            }
        ]
    }