"""
企业客户满意度提升服务

通过数据导向分析和服务优化，提升企业客户满意度至95%
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
import logging
import json

logger = logging.getLogger(__name__)

class EnterpriseCustomerSatisfactionService:
    """企业客户满意度提升服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def track_customer_satisfaction(
        self, 
        customer_id: str,
        service_type: str,
        satisfaction_score: float,
        feedback_text: Optional[str] = None,
        service_quality_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录企业客户满意度评分
        
        Args:
            customer_id: 企业客户ID
            service_type: 服务类型 (data_analysis, legal_consultation, document_review)
            satisfaction_score: 满意度评分 (1-5)
            feedback_text: 反馈文本
            service_quality_metrics: 服务质量指标
        """
        try:
            # 插入满意度记录
            insert_query = """
            INSERT INTO enterprise_customer_satisfaction (
                customer_id, service_type, satisfaction_score, 
                feedback_text, service_quality_metrics, created_at
            ) VALUES (
                :customer_id, :service_type, :satisfaction_score,
                :feedback_text, :service_quality_metrics, :created_at
            )
            """
            
            await self.db.execute(text(insert_query), {
                "customer_id": customer_id,
                "service_type": service_type,
                "satisfaction_score": satisfaction_score,
                "feedback_text": feedback_text,
                "service_quality_metrics": json.dumps(service_quality_metrics) if service_quality_metrics else None,
                "created_at": datetime.now()
            })
            
            await self.db.commit()
            
            # 检查是否需要触发改进措施
            await self._check_satisfaction_threshold(customer_id, service_type)
            
            return {
                "success": True,
                "message": "客户满意度记录成功",
                "satisfaction_score": satisfaction_score
            }
            
        except Exception as e:
            logger.error(f"记录客户满意度失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_satisfaction_analytics(
        self, 
        customer_id: Optional[str] = None,
        service_type: Optional[str] = None,
        date_range: int = 30
    ) -> Dict[str, Any]:
        """
        获取满意度分析数据
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=date_range)
            
            # 构建查询条件
            where_conditions = ["created_at >= :start_date AND created_at <= :end_date"]
            params = {"start_date": start_date, "end_date": end_date}
            
            if customer_id:
                where_conditions.append("customer_id = :customer_id")
                params["customer_id"] = customer_id
            
            if service_type:
                where_conditions.append("service_type = :service_type")
                params["service_type"] = service_type
            
            where_clause = " AND ".join(where_conditions)
            
            # 查询满意度统计
            query = f"""
            SELECT 
                COUNT(*) as total_responses,
                AVG(satisfaction_score) as avg_satisfaction,
                COUNT(CASE WHEN satisfaction_score >= 4.0 THEN 1 END) as satisfied_count,
                COUNT(CASE WHEN satisfaction_score >= 4.5 THEN 1 END) as highly_satisfied_count,
                COUNT(CASE WHEN satisfaction_score < 3.0 THEN 1 END) as dissatisfied_count,
                service_type,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM enterprise_customer_satisfaction
            WHERE {where_clause}
            GROUP BY service_type
            """
            
            result = await self.db.execute(text(query), params)
            rows = result.fetchall()
            
            if not rows:
                return self._get_empty_analytics()
            
            # 计算总体指标
            total_responses = sum(row[0] for row in rows)
            overall_avg = sum(row[0] * row[1] for row in rows) / total_responses if total_responses > 0 else 0
            total_satisfied = sum(row[2] for row in rows)
            total_highly_satisfied = sum(row[3] for row in rows)
            total_dissatisfied = sum(row[4] for row in rows)
            
            # 满意度百分比
            satisfaction_rate = (total_satisfied / total_responses * 100) if total_responses > 0 else 0
            high_satisfaction_rate = (total_highly_satisfied / total_responses * 100) if total_responses > 0 else 0
            dissatisfaction_rate = (total_dissatisfied / total_responses * 100) if total_responses > 0 else 0
            
            # 按服务类型分析
            service_analytics = {}
            for row in rows:
                service_type = row[5]
                service_analytics[service_type] = {
                    "total_responses": row[0],
                    "avg_satisfaction": round(row[1], 2),
                    "satisfaction_rate": round((row[2] / row[0] * 100), 1) if row[0] > 0 else 0,
                    "high_satisfaction_rate": round((row[3] / row[0] * 100), 1) if row[0] > 0 else 0,
                    "dissatisfaction_rate": round((row[4] / row[0] * 100), 1) if row[0] > 0 else 0
                }
            
            # 获取改进建议
            improvement_suggestions = await self._generate_improvement_suggestions(
                satisfaction_rate, service_analytics
            )
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": date_range
                },
                "overall_metrics": {
                    "total_responses": total_responses,
                    "avg_satisfaction_score": round(overall_avg, 2),
                    "satisfaction_rate_percent": round(satisfaction_rate, 1),
                    "high_satisfaction_rate_percent": round(high_satisfaction_rate, 1),
                    "dissatisfaction_rate_percent": round(dissatisfaction_rate, 1),
                    "unique_customers": sum(row[6] for row in rows)
                },
                "service_breakdown": service_analytics,
                "improvement_suggestions": improvement_suggestions,
                "target_achievement": {
                    "target_satisfaction_rate": 95.0,
                    "current_satisfaction_rate": round(satisfaction_rate, 1),
                    "gap_to_target": round(95.0 - satisfaction_rate, 1),
                    "on_track": satisfaction_rate >= 90.0
                },
                "data_disclaimer": {
                    "title": "数据说明",
                    "content": [
                        "满意度数据基于客户主动反馈，仅供参考",
                        "数据分析用于服务改进，不构成服务质量承诺",
                        "实际服务体验可能因具体需求而异"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"获取满意度分析失败: {str(e)}")
            return self._get_empty_analytics()
    
    async def get_customer_feedback_trends(
        self, 
        customer_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        获取特定客户的满意度趋势
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=months * 30)
            
            query = """
            SELECT 
                DATE_TRUNC('month', created_at) as month,
                AVG(satisfaction_score) as avg_score,
                COUNT(*) as response_count,
                service_type
            FROM enterprise_customer_satisfaction
            WHERE customer_id = :customer_id
            AND created_at >= :start_date
            GROUP BY DATE_TRUNC('month', created_at), service_type
            ORDER BY month DESC
            """
            
            result = await self.db.execute(text(query), {
                "customer_id": customer_id,
                "start_date": start_date
            })
            rows = result.fetchall()
            
            # 组织趋势数据
            trends = {}
            for row in rows:
                month_key = row[0].strftime("%Y-%m")
                service_type = row[3]
                
                if month_key not in trends:
                    trends[month_key] = {}
                
                trends[month_key][service_type] = {
                    "avg_satisfaction": round(row[1], 2),
                    "response_count": row[2]
                }
            
            # 获取最近的反馈
            recent_feedback = await self._get_recent_feedback(customer_id, limit=5)
            
            return {
                "customer_id": customer_id,
                "period_months": months,
                "satisfaction_trends": trends,
                "recent_feedback": recent_feedback,
                "trend_analysis": await self._analyze_satisfaction_trend(customer_id, months)
            }
            
        except Exception as e:
            logger.error(f"获取客户满意度趋势失败: {str(e)}")
            return {"error": "获取趋势数据失败"}
    
    async def implement_satisfaction_improvement(
        self, 
        customer_id: str,
        improvement_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        实施满意度改进措施
        """
        try:
            # 记录改进措施
            for action in improvement_actions:
                insert_query = """
                INSERT INTO customer_satisfaction_improvements (
                    customer_id, improvement_type, description, 
                    expected_impact, implementation_date, status
                ) VALUES (
                    :customer_id, :improvement_type, :description,
                    :expected_impact, :implementation_date, :status
                )
                """
                
                await self.db.execute(text(insert_query), {
                    "customer_id": customer_id,
                    "improvement_type": action.get("type"),
                    "description": action.get("description"),
                    "expected_impact": action.get("expected_impact"),
                    "implementation_date": datetime.now(),
                    "status": "planned"
                })
            
            await self.db.commit()
            
            # 创建跟踪任务
            await self._create_improvement_tracking_tasks(customer_id, improvement_actions)
            
            return {
                "success": True,
                "message": f"已为客户 {customer_id} 制定 {len(improvement_actions)} 项改进措施",
                "improvement_count": len(improvement_actions)
            }
            
        except Exception as e:
            logger.error(f"实施满意度改进措施失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def _check_satisfaction_threshold(self, customer_id: str, service_type: str):
        """检查满意度阈值，触发改进措施"""
        try:
            # 获取最近30天的满意度
            query = """
            SELECT AVG(satisfaction_score) as avg_score, COUNT(*) as count
            FROM enterprise_customer_satisfaction
            WHERE customer_id = :customer_id 
            AND service_type = :service_type
            AND created_at >= :start_date
            """
            
            start_date = datetime.now() - timedelta(days=30)
            result = await self.db.execute(text(query), {
                "customer_id": customer_id,
                "service_type": service_type,
                "start_date": start_date
            })
            row = result.fetchone()
            
            if row and row[0] and row[1] >= 3:  # 至少3次评价
                avg_score = row[0]
                if avg_score < 3.5:  # 满意度低于3.5
                    await self._trigger_improvement_alert(customer_id, service_type, avg_score)
                    
        except Exception as e:
            logger.error(f"检查满意度阈值失败: {str(e)}")
    
    async def _trigger_improvement_alert(self, customer_id: str, service_type: str, avg_score: float):
        """触发改进警报"""
        try:
            alert_query = """
            INSERT INTO customer_satisfaction_alerts (
                customer_id, service_type, avg_satisfaction_score,
                alert_type, alert_message, created_at, status
            ) VALUES (
                :customer_id, :service_type, :avg_score,
                :alert_type, :alert_message, :created_at, :status
            )
            """
            
            await self.db.execute(text(alert_query), {
                "customer_id": customer_id,
                "service_type": service_type,
                "avg_score": avg_score,
                "alert_type": "low_satisfaction",
                "alert_message": f"客户 {customer_id} 在 {service_type} 服务的满意度较低 ({avg_score:.1f}/5.0)",
                "created_at": datetime.now(),
                "status": "active"
            })
            
            await self.db.commit()
            logger.info(f"已为客户 {customer_id} 创建满意度改进警报")
            
        except Exception as e:
            logger.error(f"创建改进警报失败: {str(e)}")
    
    async def _generate_improvement_suggestions(
        self, 
        satisfaction_rate: float, 
        service_analytics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成改进建议"""
        suggestions = []
        
        # 基于整体满意度的建议
        if satisfaction_rate < 95.0:
            gap = 95.0 - satisfaction_rate
            suggestions.append({
                "priority": "high",
                "category": "overall_improvement",
                "title": "提升整体满意度",
                "description": f"当前满意度为 {satisfaction_rate:.1f}%，距离目标95%还有 {gap:.1f}% 的差距",
                "actions": [
                    "加强客户服务培训",
                    "优化服务流程",
                    "增加客户沟通频次",
                    "建立快速响应机制"
                ]
            })
        
        # 基于服务类型的建议
        for service_type, metrics in service_analytics.items():
            if metrics["satisfaction_rate"] < 90.0:
                suggestions.append({
                    "priority": "medium",
                    "category": "service_specific",
                    "title": f"改进{service_type}服务",
                    "description": f"{service_type}服务满意度为 {metrics['satisfaction_rate']:.1f}%，需要重点改进",
                    "actions": [
                        f"分析{service_type}服务的具体问题",
                        "收集更多客户反馈",
                        "优化服务交付流程",
                        "提升服务质量标准"
                    ]
                })
        
        # 基于不满意率的建议
        for service_type, metrics in service_analytics.items():
            if metrics["dissatisfaction_rate"] > 10.0:
                suggestions.append({
                    "priority": "high",
                    "category": "dissatisfaction_reduction",
                    "title": f"降低{service_type}不满意率",
                    "description": f"{service_type}服务不满意率为 {metrics['dissatisfaction_rate']:.1f}%，需要紧急处理",
                    "actions": [
                        "立即联系不满意客户",
                        "了解具体问题并制定解决方案",
                        "建立服务质量监控机制",
                        "定期回访和跟进"
                    ]
                })
        
        return suggestions
    
    async def _get_recent_feedback(self, customer_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近的客户反馈"""
        try:
            query = """
            SELECT satisfaction_score, feedback_text, service_type, created_at
            FROM enterprise_customer_satisfaction
            WHERE customer_id = :customer_id
            ORDER BY created_at DESC
            LIMIT :limit
            """
            
            result = await self.db.execute(text(query), {
                "customer_id": customer_id,
                "limit": limit
            })
            rows = result.fetchall()
            
            return [
                {
                    "satisfaction_score": row[0],
                    "feedback_text": row[1],
                    "service_type": row[2],
                    "created_at": row[3].isoformat() if row[3] else None
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"获取最近反馈失败: {str(e)}")
            return []
    
    async def _analyze_satisfaction_trend(self, customer_id: str, months: int) -> Dict[str, Any]:
        """分析满意度趋势"""
        try:
            query = """
            SELECT 
                DATE_TRUNC('month', created_at) as month,
                AVG(satisfaction_score) as avg_score
            FROM enterprise_customer_satisfaction
            WHERE customer_id = :customer_id
            AND created_at >= :start_date
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month ASC
            """
            
            start_date = datetime.now() - timedelta(days=months * 30)
            result = await self.db.execute(text(query), {
                "customer_id": customer_id,
                "start_date": start_date
            })
            rows = result.fetchall()
            
            if len(rows) < 2:
                return {"trend": "insufficient_data", "message": "数据不足以分析趋势"}
            
            # 计算趋势
            scores = [row[1] for row in rows]
            first_half = scores[:len(scores)//2]
            second_half = scores[len(scores)//2:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            if second_avg > first_avg + 0.2:
                trend = "improving"
                message = "满意度呈上升趋势"
            elif second_avg < first_avg - 0.2:
                trend = "declining"
                message = "满意度呈下降趋势，需要关注"
            else:
                trend = "stable"
                message = "满意度保持稳定"
            
            return {
                "trend": trend,
                "message": message,
                "first_period_avg": round(first_avg, 2),
                "second_period_avg": round(second_avg, 2),
                "change": round(second_avg - first_avg, 2)
            }
            
        except Exception as e:
            logger.error(f"分析满意度趋势失败: {str(e)}")
            return {"trend": "error", "message": "趋势分析失败"}
    
    async def _create_improvement_tracking_tasks(
        self, 
        customer_id: str, 
        improvement_actions: List[Dict[str, Any]]
    ):
        """创建改进跟踪任务"""
        try:
            for action in improvement_actions:
                task_query = """
                INSERT INTO customer_improvement_tasks (
                    customer_id, task_type, task_description,
                    due_date, assigned_to, status, created_at
                ) VALUES (
                    :customer_id, :task_type, :task_description,
                    :due_date, :assigned_to, :status, :created_at
                )
                """
                
                due_date = datetime.now() + timedelta(days=action.get("timeline_days", 30))
                
                await self.db.execute(text(task_query), {
                    "customer_id": customer_id,
                    "task_type": action.get("type"),
                    "task_description": action.get("description"),
                    "due_date": due_date,
                    "assigned_to": action.get("assigned_to", "customer_success_team"),
                    "status": "pending",
                    "created_at": datetime.now()
                })
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"创建改进跟踪任务失败: {str(e)}")
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """返回空的分析数据"""
        return {
            "period": {
                "start_date": datetime.now().date().isoformat(),
                "end_date": datetime.now().date().isoformat(),
                "days": 0
            },
            "overall_metrics": {
                "total_responses": 0,
                "avg_satisfaction_score": 0,
                "satisfaction_rate_percent": 0,
                "high_satisfaction_rate_percent": 0,
                "dissatisfaction_rate_percent": 0,
                "unique_customers": 0
            },
            "service_breakdown": {},
            "improvement_suggestions": [
                {
                    "priority": "high",
                    "category": "data_collection",
                    "title": "增加客户反馈收集",
                    "description": "当前缺少足够的客户满意度数据",
                    "actions": [
                        "建立定期客户满意度调研机制",
                        "在服务完成后主动收集反馈",
                        "设置满意度评价提醒"
                    ]
                }
            ],
            "target_achievement": {
                "target_satisfaction_rate": 95.0,
                "current_satisfaction_rate": 0,
                "gap_to_target": 95.0,
                "on_track": False
            },
            "data_disclaimer": {
                "title": "数据说明",
                "content": [
                    "暂无足够的满意度数据进行分析",
                    "建议增加客户反馈收集以获得更准确的分析"
                ]
            }
        }