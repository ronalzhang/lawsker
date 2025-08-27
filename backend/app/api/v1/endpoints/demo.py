"""
演示账户API端点
提供演示账户访问和数据隔离功能
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.deps import get_db
from app.services.demo_account_service import DemoAccountService
from app.services.unified_auth_service import UnifiedAuthService

logger = structlog.get_logger()

router = APIRouter()


@router.get("/demo/{demo_type}")
async def get_demo_account(
    demo_type: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取演示账户数据
    
    Args:
        demo_type: 演示类型 ('lawyer' 或 'user')
        request: 请求对象
        db: 数据库会话
    
    Returns:
        演示账户数据和访问信息
    """
    if demo_type not in ['lawyer', 'user']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="演示类型必须是 'lawyer' 或 'user'"
        )
    
    try:
        demo_service = DemoAccountService(db)
        
        # 获取演示账户数据
        demo_data = await demo_service.get_demo_account_data(demo_type)
        
        # 记录演示账户访问
        await demo_service.log_demo_activity(
            demo_data['workspace_id'],
            'access_demo',
            {
                'demo_type': demo_type,
                'ip_address': request.client.host,
                'user_agent': request.headers.get('user-agent')
            }
        )
        
        # 获取功能限制信息
        restrictions = await demo_service.get_demo_restrictions(demo_type)
        
        return {
            'success': True,
            'data': {
                'workspace_id': demo_data['workspace_id'],
                'display_name': demo_data['display_name'],
                'demo_data': demo_data['demo_data'],
                'demo_type': demo_type,
                'session_id': demo_data['session_id'],
                'is_demo': True,
                'restrictions': restrictions,
                'redirect_url': f'/{demo_type}/{demo_data["workspace_id"]}?demo=true'
            },
            'message': f'欢迎体验{demo_data["display_name"]}的工作台'
        }
        
    except Exception as e:
        logger.error("获取演示账户失败", error=str(e), demo_type=demo_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取演示账户失败，请稍后重试"
        )


@router.post("/demo/{workspace_id}/action")
async def validate_demo_action(
    workspace_id: str,
    action_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    验证演示账户操作
    
    Args:
        workspace_id: 工作台ID
        action_data: 操作数据
        request: 请求对象
        db: 数据库会话
    
    Returns:
        操作验证结果
    """
    try:
        demo_service = DemoAccountService(db)
        
        # 检查是否为演示工作台
        if not await demo_service.is_demo_workspace(workspace_id):
            return {
                'success': True,
                'allowed': True,
                'message': '非演示账户，允许所有操作'
            }
        
        action = action_data.get('action')
        session_id = action_data.get('session_id')
        
        # 验证操作
        validation_result = await demo_service.validate_demo_action(
            workspace_id, action, session_id
        )
        
        # 记录操作尝试
        await demo_service.log_demo_activity(
            workspace_id,
            f'attempt_{action}',
            {
                'allowed': validation_result['allowed'],
                'ip_address': request.client.host,
                'details': action_data
            }
        )
        
        return {
            'success': True,
            'allowed': validation_result['allowed'],
            'reason': validation_result.get('reason'),
            'suggestion': validation_result.get('suggestion'),
            'message': '操作验证完成'
        }
        
    except Exception as e:
        logger.error("验证演示操作失败", error=str(e), workspace_id=workspace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证操作失败，请稍后重试"
        )


@router.get("/demo/{workspace_id}/data")
async def get_demo_workspace_data(
    workspace_id: str,
    data_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取演示工作台数据
    
    Args:
        workspace_id: 工作台ID
        data_type: 数据类型 (可选)
        db: 数据库会话
    
    Returns:
        演示工作台数据
    """
    try:
        demo_service = DemoAccountService(db)
        
        # 检查是否为演示工作台
        if not await demo_service.is_demo_workspace(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="演示工作台不存在"
            )
        
        # 根据workspace_id获取演示数据
        from sqlalchemy import select
        from app.models.unified_auth import DemoAccount
        
        result = await db.execute(
            select(DemoAccount)
            .where(DemoAccount.workspace_id == workspace_id)
        )
        
        demo_account = result.scalar_one_or_none()
        if not demo_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="演示账户不存在"
            )
        
        # 刷新演示数据
        demo_data = await demo_service.refresh_demo_data(demo_account)
        
        # 根据data_type过滤数据
        if data_type:
            if data_type in demo_data:
                filtered_data = {data_type: demo_data[data_type]}
            else:
                filtered_data = {}
        else:
            filtered_data = demo_data
        
        return {
            'success': True,
            'data': filtered_data,
            'workspace_id': workspace_id,
            'demo_type': demo_account.demo_type,
            'is_demo': True,
            'last_updated': demo_account.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取演示工作台数据失败", error=str(e), workspace_id=workspace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取数据失败，请稍后重试"
        )


@router.post("/demo/{workspace_id}/convert")
async def convert_demo_to_real_account(
    workspace_id: str,
    conversion_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    演示账户转真实账户引导
    
    Args:
        workspace_id: 演示工作台ID
        conversion_data: 转换数据
        request: 请求对象
        db: 数据库会话
    
    Returns:
        转换引导信息
    """
    try:
        demo_service = DemoAccountService(db)
        
        # 检查是否为演示工作台
        if not await demo_service.is_demo_workspace(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="非演示账户无需转换"
            )
        
        # 获取演示账户类型
        from sqlalchemy import select
        from app.models.unified_auth import DemoAccount
        
        result = await db.execute(
            select(DemoAccount.demo_type)
            .where(DemoAccount.workspace_id == workspace_id)
        )
        
        demo_type = result.scalar_one_or_none()
        if not demo_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="演示账户不存在"
            )
        
        # 记录转换意向
        await demo_service.log_demo_activity(
            workspace_id,
            'conversion_intent',
            {
                'demo_type': demo_type,
                'conversion_data': conversion_data,
                'ip_address': request.client.host
            }
        )
        
        # 生成注册引导信息
        if demo_type == 'lawyer':
            registration_guide = {
                'registration_url': '/auth/register',
                'identity_type': 'lawyer',
                'required_documents': ['律师执业证', '身份证'],
                'benefits': [
                    '接受真实案件委托',
                    '获得案件收入',
                    '建立专业声誉',
                    '使用完整平台功能'
                ],
                'next_steps': [
                    '使用邮箱注册账户',
                    '选择律师身份',
                    '上传律师执业证',
                    '等待认证审核',
                    '开始接受案件'
                ]
            }
        else:
            registration_guide = {
                'registration_url': '/auth/register',
                'identity_type': 'user',
                'required_documents': [],
                'benefits': [
                    '发布真实法律需求',
                    '获得专业法律服务',
                    '享受平台保障',
                    '使用完整平台功能'
                ],
                'next_steps': [
                    '使用邮箱注册账户',
                    '选择用户身份',
                    '完善企业信息',
                    '发布法律需求',
                    '选择合适律师'
                ]
            }
        
        return {
            'success': True,
            'data': registration_guide,
            'message': '感谢您对我们平台的兴趣，请按照指引完成注册'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("演示账户转换引导失败", error=str(e), workspace_id=workspace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="转换引导失败，请稍后重试"
        )


@router.get("/demo/health")
async def demo_system_health(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    演示系统健康检查
    
    Args:
        db: 数据库会话
    
    Returns:
        系统健康状态
    """
    try:
        demo_service = DemoAccountService(db)
        
        # 检查演示账户数量
        from sqlalchemy import select, func
        from app.models.unified_auth import DemoAccount
        
        result = await db.execute(
            select(func.count(DemoAccount.id))
            .where(DemoAccount.is_active == True)
        )
        
        active_demo_accounts = result.scalar()
        
        # 检查各类型演示账户
        result = await db.execute(
            select(DemoAccount.demo_type, func.count(DemoAccount.id))
            .where(DemoAccount.is_active == True)
            .group_by(DemoAccount.demo_type)
        )
        
        demo_types = dict(result.fetchall())
        
        return {
            'success': True,
            'data': {
                'total_active_demos': active_demo_accounts,
                'demo_types': demo_types,
                'system_status': 'healthy',
                'last_check': datetime.now().isoformat()
            },
            'message': '演示系统运行正常'
        }
        
    except Exception as e:
        logger.error("演示系统健康检查失败", error=str(e))
        return {
            'success': False,
            'data': {
                'system_status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            },
            'message': '演示系统检查失败'
        }