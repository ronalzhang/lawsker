"""
案件管理API端点
提供案件的CRUD操作、分配、状态管理等功能
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime, date

from app.core.deps import get_current_user, get_db, require_roles
from app.services.case_service import CaseService
from app.models.user import User
from app.models.case import CaseStatus


router = APIRouter()


# Pydantic 模型定义
class DebtorInfo(BaseModel):
    """债务人信息"""
    name: str = Field(..., description="债务人姓名")
    phone: Optional[str] = Field(None, description="联系电话")
    id_card: Optional[str] = Field(None, description="身份证号")
    address: Optional[str] = Field(None, description="地址")
    company: Optional[str] = Field(None, description="工作单位")


class CaseCreateRequest(BaseModel):
    """创建案件请求"""
    client_id: UUID = Field(..., description="客户ID")
    debtor_info: DebtorInfo = Field(..., description="债务人信息")
    case_amount: float = Field(..., gt=0, description="案件金额")
    sales_user_id: UUID = Field(..., description="销售人员ID")
    debt_creation_date: date = Field(..., description="债权形成日期")
    description: Optional[str] = Field(None, description="案件描述")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")


class CaseUpdateRequest(BaseModel):
    """更新案件请求"""
    description: Optional[str] = Field(None, description="案件描述")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签")


class CaseAssignRequest(BaseModel):
    """分配案件请求"""
    lawyer_id: UUID = Field(..., description="律师ID")


class CaseStatusUpdateRequest(BaseModel):
    """更新案件状态请求"""
    status: CaseStatus = Field(..., description="新状态")
    notes: Optional[str] = Field(None, description="备注")


class CaseResponse(BaseModel):
    """案件响应"""
    id: UUID
    case_number: str
    debtor_info: Dict[str, Any]
    case_amount: float
    status: CaseStatus
    assigned_to_user_id: Optional[UUID]
    sales_user_id: UUID
    debt_creation_date: date
    description: Optional[str]
    notes: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    """案件列表响应"""
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("/", response_model=CaseResponse)
async def create_case(
    request: CaseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新案件"""
    
    # 检查权限
    if current_user["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户状态异常"
        )
    
    case_service = CaseService(db)
    
    try:
        case_data = {
            "debtor_info": request.debtor_info.dict(),
            "case_amount": request.case_amount,
            "sales_user_id": request.sales_user_id,
            "debt_creation_date": request.debt_creation_date,
            "description": request.description,
            "notes": request.notes,
            "tags": request.tags
        }
        
        case = await case_service.create_case(
            tenant_id=current_user["tenant_id"],
            client_id=request.client_id,
            case_data=case_data,
            creator_id=current_user["id"]
        )
        
        return CaseResponse.from_orm(case)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建案件失败"
        )


@router.get("/", response_model=CaseListResponse)
async def get_cases_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[CaseStatus] = Query(None, description="状态过滤"),
    assigned_to: Optional[UUID] = Query(None, description="分配给律师ID"),
    client_id: Optional[UUID] = Query(None, description="客户ID"),
    amount_min: Optional[float] = Query(None, description="最小金额"),
    amount_max: Optional[float] = Query(None, description="最大金额"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取案件列表"""
    
    case_service = CaseService(db)
    
    # 构建过滤条件
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if client_id:
        filters["client_id"] = client_id
    if amount_min:
        filters["amount_min"] = amount_min
    if amount_max:
        filters["amount_max"] = amount_max
    if keyword:
        filters["keyword"] = keyword
    
    try:
        result = await case_service.get_cases_list(
            tenant_id=current_user["tenant_id"],
            page=page,
            page_size=page_size,
            filters=filters if filters else None
        )
        
        return CaseListResponse(
            items=[CaseResponse.from_orm(case) for case in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
        
    except Exception as e:
        # 记录具体错误信息以便调试
        import traceback
        print(f"Cases API error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取案件列表失败: {str(e)}"
        )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_detail(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取案件详情"""
    
    case_service = CaseService(db)
    
    try:
        case = await case_service.get_case_by_id(case_id, current_user["tenant_id"])
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="案件不存在"
            )
        
        return CaseResponse.from_orm(case)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取案件详情失败"
        )


@router.post("/{case_id}/assign", response_model=CaseResponse)
async def assign_case(
    case_id: UUID,
    request: CaseAssignRequest,
    current_user: User = Depends(require_roles(["admin", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """分配案件给律师"""
    
    case_service = CaseService(db)
    
    try:
        case = await case_service.assign_case(
            case_id=case_id,
            lawyer_id=request.lawyer_id,
            assigner_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        
        return CaseResponse.from_orm(case)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配案件失败"
        )


@router.post("/{case_id}/smart-assign", response_model=CaseResponse)
async def smart_assign_case(
    case_id: UUID,
    current_user: User = Depends(require_roles(["admin", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """智能分配案件"""
    
    case_service = CaseService(db)
    
    try:
        case = await case_service.smart_assign_case(
            case_id=case_id,
            tenant_id=current_user.tenant_id,
            assigner_id=current_user.id
        )
        
        return CaseResponse.from_orm(case)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="智能分配案件失败"
        )


@router.patch("/{case_id}/status", response_model=CaseResponse)
async def update_case_status(
    case_id: UUID,
    request: CaseStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新案件状态"""
    
    case_service = CaseService(db)
    
    try:
        case = await case_service.update_case_status(
            case_id=case_id,
            new_status=request.status,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            notes=request.notes
        )
        
        return CaseResponse.from_orm(case)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新案件状态失败"
        )


@router.get("/statistics/overview")
async def get_case_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取案件统计信息"""
    
    case_service = CaseService(db)
    
    try:
        stats = await case_service.get_case_statistics(current_user.tenant_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )


@router.get("/lawyers/{lawyer_id}/workload")
async def get_lawyer_workload(
    lawyer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取律师工作负荷"""
    
    case_service = CaseService(db)
    
    try:
        workload = await case_service.get_lawyer_workload(
            lawyer_id=lawyer_id,
            tenant_id=current_user.tenant_id
        )
        return workload
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取律师工作负荷失败"
        ) 