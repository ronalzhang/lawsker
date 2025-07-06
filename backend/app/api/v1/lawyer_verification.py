from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from ...core.database import get_db
from ...models.user import User
from ...services.lawyer_verification_service import LawyerVerificationService

router = APIRouter()

class LawyerVerificationRequest(BaseModel):
    name: str
    law_firm: str
    license_number: str
    practice_area: str
    phone: str = ""
    email: str = ""
    years_of_practice: int = 0
    education: str = ""
    specialization: str = ""

class LawyerVerificationResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]

@router.post("/verify", response_model=LawyerVerificationResponse)
async def verify_lawyer(
    request: LawyerVerificationRequest,
    db: Session = Depends(get_db)
):
    """律师信息验证"""
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

@router.get("/check-qualification")
async def check_lawyer_qualification(
    name: str,
    law_firm: str,
    license_number: str,
    practice_area: str,
    years_of_practice: int = 0,
    education: str = "",
    phone: str = "",
    email: str = ""
):
    """检查律师资格"""
    try:
        service = LawyerVerificationService()
        
        lawyer_data = {
            'name': name,
            'law_firm': law_firm,
            'license_number': license_number,
            'practice_area': practice_area,
            'years_of_practice': years_of_practice,
            'education': education,
            'phone': phone,
            'email': email
        }
        
        qualification_check = service.check_lawyer_qualification(lawyer_data)
        
        return {
            "success": True,
            "data": qualification_check
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"资格检查失败: {str(e)}"
        )

@router.get("/verification-guide")
async def get_verification_guide():
    """获取律师认证指南"""
    try:
        service = LawyerVerificationService()
        suggestions = service.get_verification_suggestions()
        
        return {
            "success": True,
            "message": "获取认证指南成功",
            "data": suggestions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取指南失败: {str(e)}"
        )

@router.post("/verify-license")
async def verify_license_online(
    license_number: str,
    name: str
):
    """在线验证律师证"""
    try:
        service = LawyerVerificationService()
        verification_result = service.verify_license_online(license_number, name)
        
        return {
            "success": True,
            "message": "律师证验证完成",
            "data": verification_result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"律师证验证失败: {str(e)}"
        ) 