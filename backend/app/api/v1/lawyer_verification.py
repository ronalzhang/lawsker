"""
律师认证API端点
支持AI识别律师证、信息验证、资格评分等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.services.lawyer_verification_service import LawyerVerificationService
from app.services.ai_ocr_service import AIDocumentOCRService
from app.models.user import LawyerQualification, User

router = APIRouter()

# 请求模型
class LawyerVerificationRequest(BaseModel):
    name: str
    law_firm: str
    license_number: str
    experience_years: Optional[int] = 0
    specialization: str
    phone: str
    email: str
    education: str
    gender: Optional[str] = None
    id_card_number: Optional[str] = None
    license_authority: Optional[str] = None
    license_issued_date: Optional[str] = None

class LawyerCertificationRequest(BaseModel):
    """律师认证申请"""
    user_id: str
    extracted_info: dict
    additional_info: Optional[dict] = None

# 响应模型
class LawyerVerificationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

@router.post("/extract-license-info", response_model=LawyerVerificationResponse)
async def extract_license_info(
    license_image: UploadFile = File(..., description="律师证图片")
):
    """
    AI识别律师证信息
    """
    try:
        ocr_service = AIDocumentOCRService()
        
        # 验证文件类型
        if not license_image.content_type or not license_image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传图片文件"
            )
        
        # 提取律师证信息
        extraction_result = await ocr_service.extract_lawyer_license_info(license_image)
        
        if extraction_result['success']:
            # 获取提取模板供前端参考
            template = ocr_service.get_extraction_template()
            
            return LawyerVerificationResponse(
                success=True,
                message="律师证信息识别成功",
                data={
                    "extraction_result": extraction_result,
                    "template": template,
                    "suggestions": {
                        "confidence_level": "高" if extraction_result['confidence_score'] >= 80 else 
                                          "中" if extraction_result['confidence_score'] >= 60 else "低",
                        "next_steps": [
                            "请核对识别结果的准确性",
                            "补充或修正不准确的信息",
                            "确认无误后提交认证申请"
                        ]
                    }
                }
            )
        else:
            return LawyerVerificationResponse(
                success=False,
                message=f"律师证信息识别失败: {extraction_result.get('error', '未知错误')}",
                data={"error_details": extraction_result}
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )

@router.post("/batch-extract", response_model=LawyerVerificationResponse)
async def batch_extract_license_info(
    license_images: List[UploadFile] = File(..., description="多个律师证图片")
):
    """
    批量AI识别律师证信息
    """
    try:
        ocr_service = AIDocumentOCRService()
        
        # 验证文件数量
        if len(license_images) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="单次最多上传10个文件"
            )
        
        # 批量提取信息
        batch_results = await ocr_service.batch_extract_lawyer_info(license_images)
        
        # 统计结果
        success_count = sum(1 for result in batch_results if result['result']['success'])
        total_count = len(batch_results)
        
        return LawyerVerificationResponse(
            success=True,
            message=f"批量识别完成，成功{success_count}/{total_count}个文件",
            data={
                "batch_results": batch_results,
                "summary": {
                    "total_files": total_count,
                    "success_count": success_count,
                    "failure_count": total_count - success_count,
                    "success_rate": f"{(success_count/total_count*100):.1f}%" if total_count > 0 else "0%"
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量处理失败: {str(e)}"
        )

@router.post("/submit-certification", response_model=LawyerVerificationResponse)
async def submit_lawyer_certification(
    request: LawyerCertificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    提交律师认证申请
    """
    try:
        from sqlalchemy import select
        service = LawyerVerificationService()
        
        # 验证用户是否存在（演示模式可以跳过用户验证）
        is_demo_mode = (request.user_id.startswith('lawyer-') and 
                       ('-demo' in request.user_id or request.user_id.count('-') >= 2))
        
        if not is_demo_mode:
            user_query = select(User).where(User.id == request.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
        else:
            # 演示模式：不验证用户存在性
            print(f"演示模式认证，用户ID: {request.user_id}")
            user = None
        
        # 演示模式直接返回成功信息
        if is_demo_mode:
            return LawyerVerificationResponse(
                success=True,
                message="律师认证申请提交成功（演示模式）",
                data={
                    "qualification_id": f"demo-{request.user_id}",
                    "status": "pending",
                    "next_steps": [
                        "认证申请已提交（演示模式）",
                        "演示模式不会真正保存数据",
                        "实际使用时请登录真实账户"
                    ]
                }
            )
        
        # 检查是否已有认证记录
        existing_query = select(LawyerQualification).where(
            LawyerQualification.user_id == request.user_id
        )
        existing_result = await db.execute(existing_query)
        existing_qualification = existing_result.scalar_one_or_none()
        
        if existing_qualification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户已有律师认证记录"
            )
        
        # 创建认证记录
        qualification_data = service.create_lawyer_qualification(
            user_id=request.user_id,
            extracted_info=request.extracted_info,
            additional_info=request.additional_info or {}
        )
        
        # 保存到数据库
        new_qualification = LawyerQualification(**qualification_data)
        db.add(new_qualification)
        await db.commit()
        await db.refresh(new_qualification)
        
        return LawyerVerificationResponse(
            success=True,
            message="律师认证申请提交成功",
            data={
                "qualification_id": str(new_qualification.id),
                "status": new_qualification.qualification_status.value,
                "next_steps": [
                    "认证申请已提交",
                    "等待管理员审核",
                    "审核结果将通过邮件通知"
                ]
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交认证申请失败: {str(e)}"
        )

@router.get("/qualification/{user_id}", response_model=LawyerVerificationResponse)
async def get_lawyer_qualification(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取律师认证信息
    """
    try:
        from sqlalchemy import select
        qualification_query = select(LawyerQualification).where(
            LawyerQualification.user_id == user_id
        )
        qualification_result = await db.execute(qualification_query)
        qualification = qualification_result.scalar_one_or_none()
        
        if not qualification:
            return LawyerVerificationResponse(
                success=False,
                message="未找到律师认证记录",
                data=None
            )
        
        # 计算执业年限（如果发证日期存在）
        years_of_practice = 0
        if qualification.license_issued_date is not None:
            years_of_practice = (datetime.now().date() - qualification.license_issued_date).days // 365
        
        qualification_data = {
            "id": str(qualification.id),
            "user_id": str(qualification.user_id),
            "lawyer_name": qualification.lawyer_name,
            "gender": qualification.gender,
            "id_card_number": qualification.id_card_number,
            "license_number": qualification.license_number,
            "license_authority": qualification.license_authority,
            "license_issued_date": qualification.license_issued_date.isoformat() if qualification.license_issued_date is not None else None,
            "law_firm_name": qualification.law_firm_name,
            "practice_areas": qualification.practice_areas,
            "years_of_practice": years_of_practice,
            "qualification_status": qualification.qualification_status.value,
            "ai_verification_score": qualification.ai_verification_score,
            "total_cases_handled": qualification.total_cases_handled,
            "success_rate": qualification.success_rate,
            "average_rating": qualification.average_rating,
            "created_at": qualification.created_at.isoformat(),
            "updated_at": qualification.updated_at.isoformat()
        }
        
        return LawyerVerificationResponse(
            success=True,
            message="获取律师认证信息成功",
            data=qualification_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取认证信息失败: {str(e)}"
        )

@router.post("/verify", response_model=LawyerVerificationResponse)
async def verify_lawyer(
    request: LawyerVerificationRequest,
    db: Session = Depends(get_db)
):
    """律师信息验证（保留原有功能）"""
    try:
        service = LawyerVerificationService()
        
        # 验证基本信息
        lawyer_data = service.validate_lawyer_info(request.dict())
        
        # 在线验证律师证
        verification_result = service.verify_license_online(
            license_number=lawyer_data['license_number'],
            name=lawyer_data['name']
        )
        
        # 检查资格
        qualification_check = service.check_lawyer_qualification(lawyer_data)
        
        # 创建验证记录
        verification_record = service.create_verification_record(
            lawyer_data, verification_result
        )
        
        return LawyerVerificationResponse(
            success=True,
            message="律师信息验证完成",
            data={
                "lawyer_info": lawyer_data,
                "verification_result": verification_result,
                "qualification_check": qualification_check,
                "verification_record": verification_record
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证失败: {str(e)}"
        )

@router.get("/check-qualification", response_model=LawyerVerificationResponse)
async def check_lawyer_qualification(
    license_number: str,
    db: AsyncSession = Depends(get_db)
):
    """检查律师资格"""
    try:
        from sqlalchemy import select
        service = LawyerVerificationService()
        
        # 检查数据库中是否存在该律师证号
        existing_query = select(LawyerQualification).where(
            LawyerQualification.license_number == license_number
        )
        existing_result = await db.execute(existing_query)
        existing_qualification = existing_result.scalar_one_or_none()
        
        if existing_qualification:
            return LawyerVerificationResponse(
                success=True,
                message="律师资格检查完成",
                data={
                    "license_exists": True,
                    "qualification_status": existing_qualification.qualification_status.value,
                    "lawyer_name": existing_qualification.lawyer_name,
                    "law_firm": existing_qualification.law_firm_name,
                    "verification_score": existing_qualification.ai_verification_score
                }
            )
        
        # 在线验证
        online_check = service.verify_license_online(license_number, "")
        
        return LawyerVerificationResponse(
            success=True,
            message="律师资格检查完成",
            data={
                "license_exists": False,
                "online_verification": online_check
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"资格检查失败: {str(e)}"
        )

@router.get("/verification-guide", response_model=LawyerVerificationResponse)
async def get_verification_guide():
    """获取认证指南"""
    try:
        guide_data = {
            "required_documents": [
                "律师执业证书（清晰照片或扫描件）",
                "身份证明（身份证正反面）",
                "律师事务所执业许可证",
                "最近一年的执业记录"
            ],
            "verification_process": [
                "上传律师证图片进行AI识别",
                "核对并完善识别结果",
                "提交认证申请",
                "等待管理员审核",
                "认证完成，获得律师权限"
            ],
            "ai_recognition_features": [
                "自动识别律师证上的关键信息",
                "智能提取姓名、性别、身份证号",
                "自动识别执业证号和发证机关",
                "计算执业年限和验证信息准确性",
                "提供置信度评分和修正建议"
            ],
            "api_recommendations": [
                {
                    "name": "全国律师协会查询系统",
                    "url": "https://www.acla.org.cn/lawyer/search",
                    "description": "官方律师信息查询平台"
                },
                {
                    "name": "各地律师协会查询",
                    "url": "https://www.localbar.org/search",
                    "description": "地方律师协会查询系统"
                },
                {
                    "name": "司法部律师查询",
                    "url": "https://www.moj.gov.cn/lawyer",
                    "description": "司法部官方律师查询"
                }
            ],
            "verification_tips": [
                "确保律师证图片清晰可见",
                "避免反光和阴影影响识别",
                "如AI识别有误，请手动修正",
                "律师证号可通过官方网站查询验证",
                "律师事务所信息可通过工商系统核实",
                "执业年限可通过律师协会记录确认",
                "专业资质可通过案例和证书验证",
                "建议定期更新律师信息和资质"
            ]
        }
        
        return LawyerVerificationResponse(
            success=True,
            message="获取认证指南成功",
            data=guide_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取认证指南失败: {str(e)}"
        )

@router.post("/verify-license", response_model=LawyerVerificationResponse)
async def verify_license(
    license_data: dict,
    db: Session = Depends(get_db)
):
    """在线验证律师证"""
    try:
        service = LawyerVerificationService()
        
        license_number = license_data.get('license_number')
        if not license_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少律师证号"
            )
        
        verification_result = service.verify_license_online(
            license_number=license_number,
            name=license_data.get('name', '')
        )
        
        return LawyerVerificationResponse(
            success=True,
            message="律师证验证完成",
            data=verification_result
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"证号验证失败: {str(e)}"
        ) 