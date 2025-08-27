"""
批量任务滥用监控服务
实现滥用检测、统计分析、90%减少目标跟踪
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from uuid import UUID
import json
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class AbuseLevel(Enum):
    """滥用等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AbusePattern:
    """滥用模式"""
    pattern_type: str
    severity: AbuseLevel
    description: str
    indicators: Dict[str, Any]
    confidence_score: float


@dataclass
class AbuseMetrics:
    """滥用指标"""
    period_start: date
    period_end: date
    total_batch_uploads: int
    abusive_uploads: int
    abuse_rate: float
    credits_prevented_abuse: int
    estimated_cost_savings: Decimal


class BatchAbuseMonitor:
    """批量任务滥用监控服务"""
    
    def __init__(self):
        # 滥用检测阈值配置
        self.ABUSE_THRESHOLDS = {
            'daily_upload_limit': 50,  # 每日上传限制
            'hourly_upload_limit': 10,  # 每小时上传限制
            'empty_file_ratio': 0.3,   # 空文件比例阈值
            'duplicate_content_ratio': 0.5,  # 重复内容比例阈值
            'rapid_succession_minutes': 5,   # 快速连续上传时间窗口
            'suspicious_file_patterns': [    # 可疑文件模式
                'test', 'spam', 'fake', '测试', '垃圾', '假的'
            ]
        }
        
        # Credits系统实施前的基准数据（用于计算90%减少）
        self.BASELINE_ABUSE_RATE = 0.25  # 假设实施前25%的批量上传是滥用
        self.TARGET_REDUCTION = 0.90     # 目标减少90%
    
    async def detect_abuse_patterns(self, user_id: UUID, db: Session) -> List[AbusePattern]:
        """
        检测用户的滥用模式
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            检测到的滥用模式列表
        """
        try:
            patterns = []
            
            # 1. 检测频率滥用
            frequency_pattern = await self._detect_frequency_abuse(user_id, db)
            if frequency_pattern:
                patterns.append(frequency_pattern)
            
            # 2. 检测内容质量滥用
            quality_pattern = await self._detect_quality_abuse(user_id, db)
            if quality_pattern:
                patterns.append(quality_pattern)
            
            # 3. 检测重复内容滥用
            duplicate_pattern = await self._detect_duplicate_abuse(user_id, db)
            if duplicate_pattern:
                patterns.append(duplicate_pattern)
            
            # 4. 检测可疑文件名模式
            filename_pattern = await self._detect_filename_abuse(user_id, db)
            if filename_pattern:
                patterns.append(filename_pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"检测滥用模式失败: {str(e)}")
            return []
    
    async def _detect_frequency_abuse(self, user_id: UUID, db: Session) -> Optional[AbusePattern]:
        """检测频率滥用"""
        try:
            # 检查过去24小时的上传次数
            query = text("""
                SELECT COUNT(*) as daily_count,
                       COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as hourly_count
                FROM batch_upload_tasks 
                WHERE user_id = :user_id 
                AND created_at > NOW() - INTERVAL '24 hours'
            """)
            
            result = db.execute(query, {"user_id": str(user_id)}).fetchone()
            
            if not result:
                return None
            
            daily_count, hourly_count = result
            
            # 判断是否超过阈值
            if daily_count > self.ABUSE_THRESHOLDS['daily_upload_limit']:
                return AbusePattern(
                    pattern_type="frequency_abuse_daily",
                    severity=AbuseLevel.HIGH,
                    description=f"用户24小时内上传{daily_count}次，超过限制{self.ABUSE_THRESHOLDS['daily_upload_limit']}次",
                    indicators={"daily_count": daily_count, "limit": self.ABUSE_THRESHOLDS['daily_upload_limit']},
                    confidence_score=0.9
                )
            
            if hourly_count > self.ABUSE_THRESHOLDS['hourly_upload_limit']:
                return AbusePattern(
                    pattern_type="frequency_abuse_hourly",
                    severity=AbuseLevel.MEDIUM,
                    description=f"用户1小时内上传{hourly_count}次，超过限制{self.ABUSE_THRESHOLDS['hourly_upload_limit']}次",
                    indicators={"hourly_count": hourly_count, "limit": self.ABUSE_THRESHOLDS['hourly_upload_limit']},
                    confidence_score=0.8
                )
            
            return None
            
        except Exception as e:
            logger.error(f"检测频率滥用失败: {str(e)}")
            return None
    
    async def _detect_quality_abuse(self, user_id: UUID, db: Session) -> Optional[AbusePattern]:
        """检测内容质量滥用"""
        try:
            # 检查最近上传的文件质量指标
            query = text("""
                SELECT 
                    COUNT(*) as total_uploads,
                    COUNT(CASE WHEN file_size < 1024 THEN 1 END) as small_files,
                    COUNT(CASE WHEN error_records > success_records THEN 1 END) as failed_uploads
                FROM batch_upload_tasks 
                WHERE user_id = :user_id 
                AND created_at > NOW() - INTERVAL '7 days'
            """)
            
            result = db.execute(query, {"user_id": str(user_id)}).fetchone()
            
            if not result or result[0] == 0:
                return None
            
            total_uploads, small_files, failed_uploads = result
            
            # 计算质量指标
            small_file_ratio = small_files / total_uploads
            failed_ratio = failed_uploads / total_uploads
            
            if small_file_ratio > self.ABUSE_THRESHOLDS['empty_file_ratio']:
                return AbusePattern(
                    pattern_type="quality_abuse_small_files",
                    severity=AbuseLevel.MEDIUM,
                    description=f"用户上传的小文件比例过高: {small_file_ratio:.2%}",
                    indicators={
                        "small_file_ratio": small_file_ratio,
                        "threshold": self.ABUSE_THRESHOLDS['empty_file_ratio'],
                        "total_uploads": total_uploads,
                        "small_files": small_files
                    },
                    confidence_score=0.7
                )
            
            return None
            
        except Exception as e:
            logger.error(f"检测质量滥用失败: {str(e)}")
            return None
    
    async def _detect_duplicate_abuse(self, user_id: UUID, db: Session) -> Optional[AbusePattern]:
        """检测重复内容滥用"""
        try:
            # 检查文件名和大小的重复情况
            query = text("""
                SELECT 
                    file_name,
                    file_size,
                    COUNT(*) as duplicate_count
                FROM batch_upload_tasks 
                WHERE user_id = :user_id 
                AND created_at > NOW() - INTERVAL '30 days'
                GROUP BY file_name, file_size
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
            """)
            
            results = db.execute(query, {"user_id": str(user_id)}).fetchall()
            
            if not results:
                return None
            
            total_duplicates = sum(row[2] - 1 for row in results)  # 减去原始文件
            
            # 获取总上传数
            total_query = text("""
                SELECT COUNT(*) FROM batch_upload_tasks 
                WHERE user_id = :user_id 
                AND created_at > NOW() - INTERVAL '30 days'
            """)
            
            total_uploads = db.execute(total_query, {"user_id": str(user_id)}).scalar()
            
            if total_uploads > 0:
                duplicate_ratio = total_duplicates / total_uploads
                
                if duplicate_ratio > self.ABUSE_THRESHOLDS['duplicate_content_ratio']:
                    return AbusePattern(
                        pattern_type="duplicate_content_abuse",
                        severity=AbuseLevel.HIGH,
                        description=f"用户重复上传内容比例过高: {duplicate_ratio:.2%}",
                        indicators={
                            "duplicate_ratio": duplicate_ratio,
                            "threshold": self.ABUSE_THRESHOLDS['duplicate_content_ratio'],
                            "total_duplicates": total_duplicates,
                            "total_uploads": total_uploads
                        },
                        confidence_score=0.85
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"检测重复内容滥用失败: {str(e)}")
            return None
    
    async def _detect_filename_abuse(self, user_id: UUID, db: Session) -> Optional[AbusePattern]:
        """检测可疑文件名模式"""
        try:
            # 检查文件名中的可疑关键词
            suspicious_patterns = self.ABUSE_THRESHOLDS['suspicious_file_patterns']
            
            query = text("""
                SELECT file_name, COUNT(*) as count
                FROM batch_upload_tasks 
                WHERE user_id = :user_id 
                AND created_at > NOW() - INTERVAL '7 days'
                AND (
                    """ + " OR ".join([f"LOWER(file_name) LIKE '%{pattern}%'" for pattern in suspicious_patterns]) + """
                )
                GROUP BY file_name
            """)
            
            results = db.execute(query, {"user_id": str(user_id)}).fetchall()
            
            if results:
                suspicious_files = [{"filename": row[0], "count": row[1]} for row in results]
                total_suspicious = sum(row[1] for row in results)
                
                return AbusePattern(
                    pattern_type="suspicious_filename_abuse",
                    severity=AbuseLevel.MEDIUM,
                    description=f"用户上传了{total_suspicious}个可疑文件名的文件",
                    indicators={
                        "suspicious_files": suspicious_files,
                        "total_suspicious": total_suspicious,
                        "patterns_detected": suspicious_patterns
                    },
                    confidence_score=0.6
                )
            
            return None
            
        except Exception as e:
            logger.error(f"检测文件名滥用失败: {str(e)}")
            return None
    
    async def calculate_abuse_metrics(self, start_date: date, end_date: date, db: Session) -> AbuseMetrics:
        """
        计算指定时期的滥用指标
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            db: 数据库会话
            
        Returns:
            滥用指标
        """
        try:
            # 获取总批量上传数
            total_query = text("""
                SELECT COUNT(*) FROM batch_upload_tasks 
                WHERE created_at::date BETWEEN :start_date AND :end_date
                AND task_type = 'debt_collection'
            """)
            
            total_uploads = db.execute(total_query, {
                "start_date": start_date,
                "end_date": end_date
            }).scalar() or 0
            
            # 计算滥用上传数（基于多个指标）
            abuse_query = text("""
                SELECT COUNT(DISTINCT t.id) as abusive_uploads
                FROM batch_upload_tasks t
                WHERE t.created_at::date BETWEEN :start_date AND :end_date
                AND t.task_type = 'debt_collection'
                AND (
                    -- 小文件滥用
                    t.file_size < 1024
                    -- 失败率高的上传
                    OR (t.total_records > 0 AND t.error_records::float / t.total_records > 0.8)
                    -- 可疑文件名
                    OR (
                        """ + " OR ".join([f"LOWER(t.file_name) LIKE '%{pattern}%'" for pattern in self.ABUSE_THRESHOLDS['suspicious_file_patterns']]) + """
                    )
                )
            """)
            
            abusive_uploads = db.execute(abuse_query, {
                "start_date": start_date,
                "end_date": end_date
            }).scalar() or 0
            
            # 计算Credits阻止的滥用（估算）
            credits_prevented_query = text("""
                SELECT COUNT(*) FROM user_credits uc
                JOIN users u ON uc.user_id = u.id
                WHERE uc.created_at::date BETWEEN :start_date AND :end_date
                AND uc.credits_remaining = 0
                -- 假设Credits不足的用户中有一定比例会进行滥用上传
            """)
            
            credits_prevented = db.execute(credits_prevented_query, {
                "start_date": start_date,
                "end_date": end_date
            }).scalar() or 0
            
            # 估算被Credits系统阻止的滥用（基于历史数据和阈值）
            estimated_prevented_abuse = int(credits_prevented * self.BASELINE_ABUSE_RATE)
            
            # 计算滥用率
            abuse_rate = abusive_uploads / max(1, total_uploads)
            
            # 估算成本节省（每个被阻止的滥用上传节省的服务器资源成本）
            cost_per_abuse = Decimal('5.00')  # 假设每个滥用上传成本5元
            estimated_cost_savings = estimated_prevented_abuse * cost_per_abuse
            
            return AbuseMetrics(
                period_start=start_date,
                period_end=end_date,
                total_batch_uploads=total_uploads,
                abusive_uploads=abusive_uploads,
                abuse_rate=abuse_rate,
                credits_prevented_abuse=estimated_prevented_abuse,
                estimated_cost_savings=estimated_cost_savings
            )
            
        except Exception as e:
            logger.error(f"计算滥用指标失败: {str(e)}")
            return AbuseMetrics(
                period_start=start_date,
                period_end=end_date,
                total_batch_uploads=0,
                abusive_uploads=0,
                abuse_rate=0.0,
                credits_prevented_abuse=0,
                estimated_cost_savings=Decimal('0.00')
            )
    
    async def get_abuse_reduction_progress(self, db: Session) -> Dict[str, Any]:
        """
        获取滥用减少进度（90%目标跟踪）
        
        Args:
            db: 数据库会话
            
        Returns:
            滥用减少进度报告
        """
        try:
            # 获取Credits系统实施前后的数据对比
            today = date.today()
            
            # Credits系统实施前30天（假设系统在30天前实施）
            credits_implementation_date = today - timedelta(days=30)
            before_start = credits_implementation_date - timedelta(days=30)
            before_end = credits_implementation_date
            
            # Credits系统实施后30天
            after_start = credits_implementation_date
            after_end = today
            
            # 计算实施前后的指标
            before_metrics = await self.calculate_abuse_metrics(before_start, before_end, db)
            after_metrics = await self.calculate_abuse_metrics(after_start, after_end, db)
            
            # 计算减少率
            if before_metrics.abuse_rate > 0:
                actual_reduction = (before_metrics.abuse_rate - after_metrics.abuse_rate) / before_metrics.abuse_rate
            else:
                actual_reduction = 0.0
            
            # 计算目标达成率
            target_achievement = actual_reduction / self.TARGET_REDUCTION if self.TARGET_REDUCTION > 0 else 0.0
            
            return {
                "target_reduction": self.TARGET_REDUCTION,
                "actual_reduction": actual_reduction,
                "target_achievement_rate": target_achievement,
                "target_achieved": actual_reduction >= self.TARGET_REDUCTION,
                "before_period": {
                    "start_date": before_start.isoformat(),
                    "end_date": before_end.isoformat(),
                    "total_uploads": before_metrics.total_batch_uploads,
                    "abusive_uploads": before_metrics.abusive_uploads,
                    "abuse_rate": before_metrics.abuse_rate
                },
                "after_period": {
                    "start_date": after_start.isoformat(),
                    "end_date": after_end.isoformat(),
                    "total_uploads": after_metrics.total_batch_uploads,
                    "abusive_uploads": after_metrics.abusive_uploads,
                    "abuse_rate": after_metrics.abuse_rate
                },
                "credits_impact": {
                    "prevented_abuse": after_metrics.credits_prevented_abuse,
                    "cost_savings": float(after_metrics.estimated_cost_savings)
                },
                "recommendations": self._generate_recommendations(actual_reduction, target_achievement)
            }
            
        except Exception as e:
            logger.error(f"获取滥用减少进度失败: {str(e)}")
            return {
                "error": str(e),
                "target_reduction": self.TARGET_REDUCTION,
                "actual_reduction": 0.0,
                "target_achievement_rate": 0.0,
                "target_achieved": False
            }
    
    def _generate_recommendations(self, actual_reduction: float, target_achievement: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if target_achievement < 0.5:
            recommendations.extend([
                "考虑降低每周免费Credits数量",
                "提高Credits购买价格",
                "加强滥用检测算法",
                "实施更严格的文件验证"
            ])
        elif target_achievement < 0.8:
            recommendations.extend([
                "优化滥用检测阈值",
                "增加用户教育内容",
                "改进批量上传界面提示"
            ])
        elif target_achievement >= 1.0:
            recommendations.extend([
                "目标已达成，继续监控维持效果",
                "考虑适当放宽限制以提升用户体验",
                "分析成功经验用于其他功能优化"
            ])
        else:
            recommendations.extend([
                "接近目标，继续当前策略",
                "细化监控指标",
                "准备长期维护方案"
            ])
        
        return recommendations
    
    async def record_abuse_incident(self, user_id: UUID, patterns: List[AbusePattern], db: Session):
        """
        记录滥用事件
        
        Args:
            user_id: 用户ID
            patterns: 检测到的滥用模式
            db: 数据库会话
        """
        try:
            # 这里可以创建一个滥用事件记录表
            # 暂时记录到日志
            for pattern in patterns:
                logger.warning(f"检测到滥用行为: 用户={user_id}, 类型={pattern.pattern_type}, "
                             f"严重程度={pattern.severity.value}, 描述={pattern.description}")
            
            # 如果需要持久化记录，可以创建 abuse_incidents 表
            # insert_query = text("""
            #     INSERT INTO abuse_incidents (
            #         user_id, pattern_type, severity, description, 
            #         indicators, confidence_score, created_at
            #     ) VALUES (
            #         :user_id, :pattern_type, :severity, :description,
            #         :indicators, :confidence_score, NOW()
            #     )
            # """)
            
        except Exception as e:
            logger.error(f"记录滥用事件失败: {str(e)}")


# 服务实例工厂函数
def create_batch_abuse_monitor() -> BatchAbuseMonitor:
    """创建批量滥用监控服务实例"""
    return BatchAbuseMonitor()