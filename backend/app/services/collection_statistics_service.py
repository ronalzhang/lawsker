"""
催收统计服务 - 数据导向分析（仅供参考）

本服务提供催收数据的统计分析，但不构成成功率承诺。
所有数据仅供参考，不保证具体结果。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class CollectionStatisticsService:
    """催收统计服务 - 数据导向分析"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_collection_statistics(
        self, 
        institution_id: Optional[str] = None,
        date_range: int = 30
    ) -> Dict[str, Any]:
        """
        获取催收统计数据（仅供参考）
        
        重要声明：
        - 本统计数据仅供参考，不构成成功率承诺
        - 实际结果可能因案件具体情况而异
        - 平台不保证任何具体的催收成功率
        """
        try:
            # 计算日期范围
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=date_range)
            
            # 构建查询条件
            where_clause = "WHERE dr.created_at >= :start_date AND dr.created_at <= :end_date"
            params = {"start_date": start_date, "end_date": end_date}
            
            if institution_id:
                where_clause += " AND u.id = :institution_id"
                params["institution_id"] = institution_id
            
            # 查询统计数据
            query = f"""
            SELECT 
                COUNT(*) as total_cases,
                COUNT(CASE WHEN dr.status = 'completed' THEN 1 END) as completed_cases,
                COUNT(CASE WHEN dr.status = 'in_progress' THEN 1 END) as in_progress_cases,
                COUNT(CASE WHEN dr.status = 'pending' THEN 1 END) as pending_cases,
                AVG(CASE WHEN dr.status = 'completed' AND dr.response_time IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM dr.response_time) / 3600 END) as avg_response_hours,
                COUNT(CASE WHEN dr.client_feedback_rating >= 4 THEN 1 END) as positive_feedback_count,
                COUNT(CASE WHEN dr.client_feedback_rating IS NOT NULL THEN 1 END) as total_feedback_count
            FROM document_review_tasks dr
            JOIN users u ON dr.creator_id = u.id
            {where_clause}
            """
            
            result = await self.db.execute(text(query), params)
            row = result.fetchone()
            
            if not row:
                return self._get_empty_statistics()
            
            # 计算参考指标（添加免责声明）
            total_cases = row[0] or 0
            completed_cases = row[1] or 0
            positive_feedback = row[6] or 0
            total_feedback = row[7] or 0
            
            # 响应率（仅供参考）
            response_rate = (completed_cases / total_cases * 100) if total_cases > 0 else 0
            
            # 客户满意度（仅供参考）
            satisfaction_rate = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
            
            statistics = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": date_range
                },
                "case_statistics": {
                    "total_cases": total_cases,
                    "completed_cases": completed_cases,
                    "in_progress_cases": row[2] or 0,
                    "pending_cases": row[3] or 0
                },
                "reference_indicators": {
                    "response_rate_percent": round(response_rate, 1),
                    "avg_response_hours": round(row[4] or 0, 1),
                    "client_satisfaction_percent": round(satisfaction_rate, 1),
                    "total_feedback_count": total_feedback
                },
                "disclaimer": {
                    "title": "重要声明",
                    "content": [
                        "本统计数据仅供参考，不构成任何成功率承诺或保证",
                        "实际催收结果受多种因素影响，包括但不限于债务人情况、案件复杂程度等",
                        "平台提供数据分析服务，不保证任何具体的催收成功率或回收金额",
                        "所有指标均为历史数据统计，不代表未来结果",
                        "请根据具体案件情况和专业判断做出决策"
                    ]
                },
                "data_source_note": "数据来源：平台历史案件记录，统计时间范围：{} 至 {}".format(
                    start_date.strftime("%Y年%m月%d日"),
                    end_date.strftime("%Y年%m月%d日")
                )
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取催收统计数据失败: {str(e)}")
            return self._get_empty_statistics()
    
    async def get_lawyer_performance_reference(
        self, 
        lawyer_id: str,
        date_range: int = 90
    ) -> Dict[str, Any]:
        """
        获取律师表现参考数据（不构成能力保证）
        
        重要：此数据仅供参考，不代表律师未来表现或能力保证
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=date_range)
            
            query = """
            SELECT 
                COUNT(*) as total_handled,
                COUNT(CASE WHEN dr.status = 'completed' THEN 1 END) as completed_count,
                AVG(CASE WHEN dr.client_feedback_rating IS NOT NULL 
                    THEN dr.client_feedback_rating END) as avg_rating,
                COUNT(CASE WHEN dr.client_feedback_rating >= 4 THEN 1 END) as positive_reviews
            FROM document_review_tasks dr
            WHERE dr.lawyer_id = :lawyer_id
            AND dr.created_at >= :start_date 
            AND dr.created_at <= :end_date
            """
            
            result = await self.db.execute(text(query), {
                "lawyer_id": lawyer_id,
                "start_date": start_date,
                "end_date": end_date
            })
            row = result.fetchone()
            
            if not row:
                return self._get_empty_lawyer_reference()
            
            total_handled = row[0] or 0
            completed_count = row[1] or 0
            
            return {
                "lawyer_id": lawyer_id,
                "period": f"{date_range}天",
                "reference_data": {
                    "cases_handled": total_handled,
                    "completion_count": completed_count,
                    "avg_client_rating": round(row[2] or 0, 1),
                    "positive_review_count": row[3] or 0
                },
                "performance_disclaimer": {
                    "title": "律师表现数据说明",
                    "content": [
                        "以上数据仅为历史表现统计，不构成律师能力保证",
                        "律师表现受案件类型、复杂程度等多种因素影响",
                        "历史数据不代表未来表现或服务质量承诺",
                        "请结合具体案件需求选择合适的律师"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"获取律师表现参考数据失败: {str(e)}")
            return self._get_empty_lawyer_reference()
    
    def _get_empty_statistics(self) -> Dict[str, Any]:
        """返回空的统计数据结构"""
        return {
            "period": {
                "start_date": datetime.now().date().isoformat(),
                "end_date": datetime.now().date().isoformat(),
                "days": 0
            },
            "case_statistics": {
                "total_cases": 0,
                "completed_cases": 0,
                "in_progress_cases": 0,
                "pending_cases": 0
            },
            "reference_indicators": {
                "response_rate_percent": 0,
                "avg_response_hours": 0,
                "client_satisfaction_percent": 0,
                "total_feedback_count": 0
            },
            "disclaimer": {
                "title": "重要声明",
                "content": [
                    "暂无足够数据进行统计分析，仅供参考",
                    "本平台提供数据导向服务，不构成任何承诺，不保证具体结果"
                ]
            },
            "data_source_note": "数据来源：平台历史案件记录（当前无数据）"
        }
    
    def _get_empty_lawyer_reference(self) -> Dict[str, Any]:
        """返回空的律师参考数据"""
        return {
            "lawyer_id": "",
            "period": "0天",
            "reference_data": {
                "cases_handled": 0,
                "completion_count": 0,
                "avg_client_rating": 0,
                "positive_review_count": 0
            },
            "performance_disclaimer": {
                "title": "律师表现数据说明",
                "content": [
                    "暂无足够的历史数据",
                    "律师表现数据仅供参考，不构成能力保证"
                ]
            }
        }