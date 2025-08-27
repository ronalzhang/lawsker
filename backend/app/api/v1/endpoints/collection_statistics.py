"""
催收统计API - 数据导向分析（仅供参考）

重要声明：
- 本API提供的所有统计数据仅供参考
- 不构成任何成功率承诺或保证
- 实际结果可能因具体情况而异
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import logging

from app.core.deps import get_db, get_current_user
from app.services.collection_statistics_service import CollectionStatisticsService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/statistics", response_model=Dict[str, Any])
async def get_collection_statistics(
    date_range: int = Query(30, ge=1, le=365, description="统计天数范围"),
    institution_id: Optional[str] = Query(None, description="机构ID（可选）"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取催收统计数据（仅供参考）
    
    重要声明：
    - 返回的统计数据仅供参考，不构成成功率承诺
    - 实际催收结果受多种因素影响
    - 平台不保证任何具体的催收成功率
    """
    try:
        # 权限检查：只有管理员和机构用户可以查看统计
        if current_user.get("user_type") not in ["admin", "institution"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看催收统计数据"
            )
        
        # 如果是机构用户，只能查看自己的数据
        if current_user.get("user_type") == "institution":
            institution_id = current_user.get("id")
        
        service = CollectionStatisticsService(db)
        statistics = await service.get_collection_statistics(
            institution_id=institution_id,
            date_range=date_range
        )
        
        # 添加API级别的免责声明
        statistics["api_disclaimer"] = {
            "service_nature": "数据导向分析服务",
            "important_notice": [
                "本API提供的统计数据仅供参考和分析使用",
                "平台不承诺任何具体的催收成功率或回收金额",
                "所有数据基于历史记录统计，不代表未来结果",
                "请根据专业判断和具体案件情况做出决策",
                "如需专业法律建议，请咨询相关律师"
            ],
            "data_limitation": "统计数据可能受样本大小、时间范围等因素影响，仅供参考"
        }
        
        return {
            "success": True,
            "data": statistics,
            "message": "催收统计数据获取成功（仅供参考）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取催收统计数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计数据失败"
        )

@router.get("/lawyer-performance/{lawyer_id}", response_model=Dict[str, Any])
async def get_lawyer_performance_reference(
    lawyer_id: str,
    date_range: int = Query(90, ge=1, le=365, description="统计天数范围"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取律师表现参考数据（不构成能力保证）
    
    重要：此数据仅供参考，不代表律师未来表现或能力保证
    """
    try:
        # 权限检查
        if current_user.get("user_type") not in ["admin", "institution", "lawyer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看律师表现数据"
            )
        
        # 律师只能查看自己的数据
        if current_user.get("user_type") == "lawyer" and current_user.get("id") != lawyer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能查看自己的表现数据"
            )
        
        service = CollectionStatisticsService(db)
        performance_data = await service.get_lawyer_performance_reference(
            lawyer_id=lawyer_id,
            date_range=date_range
        )
        
        # 添加额外的免责声明
        performance_data["service_disclaimer"] = {
            "data_nature": "历史表现参考数据",
            "limitations": [
                "数据仅反映历史表现，不预测未来结果",
                "律师表现受案件类型、复杂程度等多种因素影响",
                "不构成律师专业能力或服务质量的保证",
                "选择律师时请综合考虑多种因素"
            ]
        }
        
        return {
            "success": True,
            "data": performance_data,
            "message": "律师表现参考数据获取成功（仅供参考）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取律师表现数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取律师表现数据失败"
        )

@router.get("/disclaimer", response_model=Dict[str, Any])
async def get_service_disclaimer():
    """
    获取催收统计服务免责声明
    """
    return {
        "service_name": "催收统计分析服务",
        "service_nature": "数据导向分析",
        "disclaimer": {
            "title": "服务免责声明",
            "content": [
                "本服务提供基于历史数据的统计分析，仅供参考使用",
                "平台不承诺、不保证任何具体的催收成功率或回收金额",
                "实际催收结果受债务人情况、案件复杂程度、法律环境等多种因素影响",
                "所有统计指标均为历史数据分析，不代表未来结果或趋势预测",
                "用户应根据专业判断和具体案件情况做出决策",
                "如需专业法律建议或催收策略，请咨询相关专业律师",
                "平台仅提供数据分析工具和信息服务，不承担催收结果责任"
            ]
        },
        "legal_notice": {
            "title": "法律声明",
            "content": [
                "本平台为数据分析和信息服务平台",
                "不从事具体的催收业务或法律服务",
                "所有法律服务由平台注册律师独立提供",
                "平台不对律师服务质量或结果承担责任"
            ]
        },
        "data_accuracy": {
            "title": "数据准确性说明",
            "content": [
                "统计数据基于平台记录的历史案件信息",
                "数据准确性受录入质量、样本大小等因素影响",
                "平台努力确保数据准确性，但不保证绝对准确",
                "如发现数据异常，请及时联系客服"
            ]
        }
    }