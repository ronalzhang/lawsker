"""
统一认证系统API端点
处理邮箱验证注册、律师证认证和演示账户
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
import structlog

from app.core.deps import get_db, get_current_user
from app.services.unified_auth_service import UnifiedAuthService
from app.services.lawyer_certification_service import LawyerCertificationService

logger = structlog.get_logger()
router = APIRouter()


# Pydantic模型
class EmailRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    tenant_id: str


class OptimizedRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    identity_type: str  # 'lawyer' or 'user'
    tenant_id: str = '00000000-0000-0000-0000-000000000001'
    phone: str = None


class EmailCheckRequest(BaseModel):
    email: EmailStr


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationRequest(BaseModel):
    verification_token: str


class IdentitySelectionRequest(BaseModel):
    user_id: str
    identity_type: str  # 'lawyer' or 'user'


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class CertificationStatusResponse(BaseModel):
    status: str
    message: str
    certification_id: str = None
    lawyer_name: str = None
    license_number: str = None


@router.post("/register", summary="邮箱验证注册")
async def register_with_email_verification(
    request: EmailRegistrationRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    邮箱验证注册
    
    - **email**: 用户邮箱
    - **password**: 密码
    - **full_name**: 全名
    - **tenant_id**: 租户ID
    """
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.register_with_email_verification(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        tenant_id=request.tenant_id
    )


@router.post("/register-optimized", summary="优化的2步注册")
async def register_optimized(
    request: OptimizedRegistrationRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    优化的2步注册流程 - 合并注册和身份选择
    
    - **email**: 用户邮箱
    - **password**: 密码
    - **full_name**: 全名
    - **identity_type**: 身份类型 ('lawyer' 或 'user')
    - **tenant_id**: 租户ID
    - **phone**: 手机号（可选）
    """
    if request.identity_type not in ['lawyer', 'user']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的身份类型"
        )
    
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.register_optimized(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        identity_type=request.identity_type,
        tenant_id=request.tenant_id,
        phone=request.phone
    )


@router.post("/check-verification", summary="检查邮箱验证状态")
async def check_email_verification(
    request: EmailCheckRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    检查邮箱验证状态
    
    - **email**: 用户邮箱
    """
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.check_email_verification(request.email)


@router.post("/resend-verification", summary="重新发送验证邮件")
async def resend_verification_email(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    重新发送验证邮件
    
    - **email**: 用户邮箱
    """
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.resend_verification_email(request.email)


@router.post("/verify-email", summary="验证邮箱")
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    验证邮箱
    
    - **verification_token**: 验证令牌
    """
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.verify_email(request.verification_token)


@router.post("/set-identity", summary="设置用户身份")
async def set_user_identity(
    request: IdentitySelectionRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    设置用户身份并获取重定向信息
    
    - **user_id**: 用户ID
    - **identity_type**: 身份类型 ('lawyer' 或 'user')
    """
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.set_user_identity_and_redirect(
        user_id=request.user_id,
        identity_type=request.identity_type
    )


@router.post("/login", summary="统一登录")
async def unified_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    统一登录并获取重定向信息
    
    - **username_or_email**: 用户名或邮箱
    - **password**: 密码
    """
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.authenticate_and_redirect(
        username_or_email=request.username_or_email,
        password=request.password
    )


@router.get("/demo/{demo_type}", summary="获取演示账户数据")
async def get_demo_account(
    demo_type: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取演示账户数据
    
    - **demo_type**: 演示类型 ('lawyer' 或 'user')
    """
    if demo_type not in ['lawyer', 'user']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的演示类型"
        )
    
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.get_demo_account_data(demo_type)


# 律师证认证相关端点
@router.post("/lawyer/certification", summary="提交律师证认证")
async def submit_lawyer_certification(
    lawyer_name: str = Form(...),
    license_number: str = Form(...),
    law_firm: str = Form(None),
    practice_areas: str = Form("[]"),  # JSON字符串
    years_of_experience: int = Form(0),
    education_background: str = Form(None),
    certificate_file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    提交律师证认证申请
    
    - **lawyer_name**: 律师姓名
    - **license_number**: 执业证号
    - **law_firm**: 律师事务所
    - **practice_areas**: 执业领域（JSON数组字符串）
    - **years_of_experience**: 执业年限
    - **education_background**: 教育背景
    - **certificate_file**: 律师证文件
    """
    import json
    
    cert_service = LawyerCertificationService(db)
    
    # 解析执业领域
    try:
        practice_areas_list = json.loads(practice_areas)
    except json.JSONDecodeError:
        practice_areas_list = []
    
    cert_data = {
        'lawyer_name': lawyer_name,
        'license_number': license_number,
        'law_firm': law_firm,
        'practice_areas': practice_areas_list,
        'years_of_experience': years_of_experience,
        'education_background': education_background
    }
    
    return await cert_service.submit_certification_request(
        user_id=current_user['id'],
        cert_data=cert_data,
        certificate_file=certificate_file
    )


@router.get("/lawyer/certification/status", summary="获取认证状态")
async def get_certification_status(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CertificationStatusResponse:
    """获取当前用户的律师证认证状态"""
    cert_service = LawyerCertificationService(db)
    
    status_data = await cert_service.get_certification_status(current_user['id'])
    
    return CertificationStatusResponse(**status_data)


# 管理员审核端点
@router.get("/admin/certifications/pending", summary="获取待审核认证申请")
async def get_pending_certifications(
    limit: int = 20,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取待审核的律师证认证申请列表（管理员专用）
    
    - **limit**: 限制数量
    - **offset**: 偏移量
    """
    # 检查管理员权限
    if 'admin' not in current_user.get('roles', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    cert_service = LawyerCertificationService(db)
    
    return await cert_service.get_pending_certifications(limit, offset)


@router.post("/admin/certifications/{cert_id}/approve", summary="审核通过")
async def approve_certification(
    cert_id: str,
    review_notes: str = None,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员审核通过律师证认证
    
    - **cert_id**: 认证申请ID
    - **review_notes**: 审核备注
    """
    # 检查管理员权限
    if 'admin' not in current_user.get('roles', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    cert_service = LawyerCertificationService(db)
    
    return await cert_service.approve_certification(
        cert_id=cert_id,
        admin_id=current_user['id'],
        review_notes=review_notes
    )


@router.post("/admin/certifications/{cert_id}/reject", summary="审核拒绝")
async def reject_certification(
    cert_id: str,
    review_notes: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员审核拒绝律师证认证
    
    - **cert_id**: 认证申请ID
    - **review_notes**: 拒绝原因
    """
    # 检查管理员权限
    if 'admin' not in current_user.get('roles', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    cert_service = LawyerCertificationService(db)
    
    return await cert_service.reject_certification(
        cert_id=cert_id,
        admin_id=current_user['id'],
        review_notes=review_notes
    )


@router.get("/redirect-info/{user_id}", summary="获取用户重定向信息")
async def get_user_redirect_info(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取用户重定向信息
    
    - **user_id**: 用户ID
    """
    auth_service = UnifiedAuthService(db)
    
    return await auth_service.get_user_redirect_info(user_id)


@router.post("/check-login-status", summary="检查登录状态并获取重定向信息")
async def check_login_status(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    检查当前用户登录状态并返回重定向信息
    用于页面刷新或重新访问时的自动重定向
    """
    auth_service = UnifiedAuthService(db)
    
    redirect_info = await auth_service.get_user_redirect_info(current_user['id'])
    
    return {
        'logged_in': True,
        'user_id': current_user['id'],
        'username': current_user.get('username'),
        'email': current_user.get('email'),
        **redirect_info
    }