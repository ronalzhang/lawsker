"""
用户Credits支付控制服务
实现Credits管理、批量上传控制、防滥用机制
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import UUID
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from fastapi import HTTPException

from app.core.database import get_db
from app.services.payment_service import WeChatPayService
from app.services.config_service import SystemConfigService

logger = logging.getLogger(__name__)


class InsufficientCreditsError(Exception):
    """Credits不足异常"""
    def __init__(self, message: str, current_credits: int = 0, required_credits: int = 1):
        self.message = message
        self.current_credits = current_credits
        self.required_credits = required_credits
        super().__init__(self.message)


class UserCreditsService:
    """用户Credits支付控制服务"""
    
    def __init__(self, config_service: SystemConfigService = None, payment_service: WeChatPayService = None):
        self.config_service = config_service
        self.payment_service = payment_service
        
        # Credits配置
        self.CREDITS_PER_WEEK = 1  # 每周免费Credits
        self.CREDIT_PRICE = Decimal('50.00')  # 50元/个Credit
        self.BATCH_UPLOAD_COST = 1  # 批量上传消耗1个Credit
        
    async def initialize_user_credits(self, user_id: UUID, db: Session) -> Dict[str, Any]:
        """
        初始化用户Credits - 每周1个免费
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            初始化结果
        """
        try:
            # 检查是否已经初始化
            check_query = text("""
                SELECT user_id FROM user_credits WHERE user_id = :user_id
            """)
            
            existing = db.execute(check_query, {"user_id": str(user_id)}).fetchone()
            
            if existing:
                logger.info(f"用户 {user_id} Credits已初始化")
                return {"status": "already_initialized", "user_id": str(user_id)}
            
            # 创建Credits记录
            insert_query = text("""
                INSERT INTO user_credits (
                    user_id, credits_weekly, credits_remaining, 
                    credits_purchased, total_credits_used, last_reset_date
                ) VALUES (
                    :user_id, :credits_weekly, :credits_remaining,
                    0, 0, :reset_date
                )
            """)
            
            db.execute(insert_query, {
                "user_id": str(user_id),
                "credits_weekly": self.CREDITS_PER_WEEK,
                "credits_remaining": self.CREDITS_PER_WEEK,
                "reset_date": date.today()
            })
            
            db.commit()
            
            logger.info(f"用户 {user_id} Credits初始化成功")
            
            return {
                "status": "initialized",
                "user_id": str(user_id),
                "credits_weekly": self.CREDITS_PER_WEEK,
                "credits_remaining": self.CREDITS_PER_WEEK,
                "last_reset_date": date.today().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"初始化用户Credits失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"初始化Credits失败: {str(e)}")
    
    async def get_user_credits(self, user_id: UUID, db: Session) -> Dict[str, Any]:
        """
        获取用户Credits信息
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            Credits信息
        """
        try:
            query = text("""
                SELECT 
                    credits_weekly,
                    credits_remaining,
                    credits_purchased,
                    total_credits_used,
                    last_reset_date,
                    created_at,
                    updated_at
                FROM user_credits 
                WHERE user_id = :user_id
            """)
            
            result = db.execute(query, {"user_id": str(user_id)}).fetchone()
            
            if not result:
                # 如果没有记录，自动初始化
                return await self.initialize_user_credits(user_id, db)
            
            # 检查是否需要每周重置
            await self._check_and_reset_weekly_credits(user_id, db)
            
            # 重新查询最新数据
            result = db.execute(query, {"user_id": str(user_id)}).fetchone()
            
            return {
                "user_id": str(user_id),
                "credits_weekly": result[0],
                "credits_remaining": result[1],
                "credits_purchased": result[2],
                "total_credits_used": result[3],
                "last_reset_date": result[4].isoformat() if result[4] else None,
                "next_reset_date": self._calculate_next_reset_date(result[4]).isoformat(),
                "created_at": result[5].isoformat() if result[5] else None,
                "updated_at": result[6].isoformat() if result[6] else None
            }
            
        except Exception as e:
            logger.error(f"获取用户Credits失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取Credits信息失败: {str(e)}")
    
    async def _check_and_reset_weekly_credits(self, user_id: UUID, db: Session) -> bool:
        """
        检查并执行每周Credits重置
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            是否执行了重置
        """
        try:
            # 获取最后重置日期
            query = text("""
                SELECT last_reset_date FROM user_credits WHERE user_id = :user_id
            """)
            
            result = db.execute(query, {"user_id": str(user_id)}).fetchone()
            
            if not result:
                return False
            
            last_reset = result[0]
            today = date.today()
            
            # 计算是否需要重置（每周一重置）
            if self._should_reset_credits(last_reset, today):
                await self._reset_user_credits(user_id, db)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查Credits重置失败: {str(e)}")
            return False
    
    def _should_reset_credits(self, last_reset: date, current_date: date) -> bool:
        """
        判断是否应该重置Credits（每周一重置）
        
        Args:
            last_reset: 最后重置日期
            current_date: 当前日期
            
        Returns:
            是否应该重置
        """
        if not last_reset:
            return True
        
        # 计算上次重置日期所在周的周一
        days_since_monday = last_reset.weekday()
        last_reset_monday = last_reset - timedelta(days=days_since_monday)
        
        # 计算当前日期所在周的周一
        current_days_since_monday = current_date.weekday()
        current_monday = current_date - timedelta(days=current_days_since_monday)
        
        # 如果当前周一晚于上次重置周一，则需要重置
        return current_monday > last_reset_monday
    
    def _calculate_next_reset_date(self, last_reset: date) -> date:
        """
        计算下次重置日期（下周一）
        
        Args:
            last_reset: 最后重置日期
            
        Returns:
            下次重置日期
        """
        if not last_reset:
            today = date.today()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            return today + timedelta(days=days_until_monday)
        
        # 计算下周一
        days_since_monday = last_reset.weekday()
        last_monday = last_reset - timedelta(days=days_since_monday)
        next_monday = last_monday + timedelta(days=7)
        
        return next_monday
    
    async def _reset_user_credits(self, user_id: UUID, db: Session) -> Dict[str, Any]:
        """
        重置用户每周Credits
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            重置结果
        """
        try:
            update_query = text("""
                UPDATE user_credits 
                SET 
                    credits_remaining = credits_remaining + :weekly_credits,
                    last_reset_date = :reset_date,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """)
            
            db.execute(update_query, {
                "user_id": str(user_id),
                "weekly_credits": self.CREDITS_PER_WEEK,
                "reset_date": date.today()
            })
            
            db.commit()
            
            logger.info(f"用户 {user_id} Credits重置成功")
            
            return {
                "status": "reset_success",
                "user_id": str(user_id),
                "credits_added": self.CREDITS_PER_WEEK,
                "reset_date": date.today().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"重置用户Credits失败: {str(e)}")
            raise
    
    async def consume_credits_for_batch_upload(self, user_id: UUID, db: Session) -> Dict[str, Any]:
        """
        批量上传消耗Credits
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            消耗结果
        """
        try:
            # 检查并重置Credits
            await self._check_and_reset_weekly_credits(user_id, db)
            
            # 获取当前Credits
            user_credits = await self.get_user_credits(user_id, db)
            
            if user_credits['credits_remaining'] < self.BATCH_UPLOAD_COST:
                raise InsufficientCreditsError(
                    "Credits不足，请购买或等待每周重置",
                    current_credits=user_credits['credits_remaining'],
                    required_credits=self.BATCH_UPLOAD_COST
                )
            
            # 扣除Credits
            update_query = text("""
                UPDATE user_credits 
                SET 
                    credits_remaining = credits_remaining - :cost,
                    total_credits_used = total_credits_used + :cost,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """)
            
            db.execute(update_query, {
                "user_id": str(user_id),
                "cost": self.BATCH_UPLOAD_COST
            })
            
            # 记录使用记录和审计日志
            await self._record_credits_usage(
                user_id, self.BATCH_UPLOAD_COST, 'batch_upload', db
            )
            await self._log_audit_trail(user_id, 'credits_consumed', self.BATCH_UPLOAD_COST, {'action': 'batch_upload'}, db)
            
            db.commit()
            
            logger.info(f"用户 {user_id} 批量上传消耗 {self.BATCH_UPLOAD_COST} Credits")
            
            return {
                "status": "success",
                "credits_consumed": self.BATCH_UPLOAD_COST,
                "credits_remaining": user_credits['credits_remaining'] - self.BATCH_UPLOAD_COST,
                "usage_type": "batch_upload"
            }
            
        except InsufficientCreditsError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"消耗Credits失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"消耗Credits失败: {str(e)}")
    
    async def purchase_credits(self, user_id: UUID, credits_count: int, db: Session) -> Dict[str, Any]:
        """
        购买Credits - 50元/个
        
        Args:
            user_id: 用户ID
            credits_count: 购买数量
            db: 数据库会话
            
        Returns:
            购买结果
        """
        try:
            if credits_count <= 0 or credits_count > 100:
                raise HTTPException(status_code=400, detail="购买数量必须在1-100之间")
            
            total_amount = credits_count * self.CREDIT_PRICE
            
            # 创建购买记录
            purchase_id = str(uuid.uuid4())
            
            insert_query = text("""
                INSERT INTO credit_purchase_records (
                    id, user_id, credits_count, unit_price, 
                    total_amount, status
                ) VALUES (
                    :id, :user_id, :credits_count, :unit_price,
                    :total_amount, 'pending'
                )
            """)
            
            db.execute(insert_query, {
                "id": purchase_id,
                "user_id": str(user_id),
                "credits_count": credits_count,
                "unit_price": self.CREDIT_PRICE,
                "total_amount": total_amount
            })
            
            # 创建支付订单（如果有支付服务）
            payment_order = None
            if self.payment_service:
                try:
                    # 这里需要一个临时的case_id，实际应该创建专门的Credits支付订单
                    temp_case_id = str(uuid.uuid4())
                    payment_order = await self.payment_service.create_payment_order(
                        case_id=temp_case_id,
                        amount=total_amount,
                        description=f"购买Credits {credits_count}个",
                        user_id=user_id,
                        db=db
                    )
                    
                    # 更新购买记录的支付订单ID
                    update_query = text("""
                        UPDATE credit_purchase_records 
                        SET payment_order_id = :order_id
                        WHERE id = :purchase_id
                    """)
                    
                    db.execute(update_query, {
                        "order_id": payment_order.get('order_no'),
                        "purchase_id": purchase_id
                    })
                    
                except Exception as e:
                    logger.warning(f"创建支付订单失败: {str(e)}")
            
            db.commit()
            
            return {
                "status": "pending_payment",
                "purchase_id": purchase_id,
                "credits_count": credits_count,
                "unit_price": float(self.CREDIT_PRICE),
                "total_amount": float(total_amount),
                "payment_order": payment_order
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"购买Credits失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"购买Credits失败: {str(e)}")
    
    async def confirm_credits_purchase(self, purchase_id: str, db: Session) -> Dict[str, Any]:
        """
        确认Credits购买（支付成功后调用）
        
        Args:
            purchase_id: 购买记录ID
            db: 数据库会话
            
        Returns:
            确认结果
        """
        try:
            # 获取购买记录
            query = text("""
                SELECT user_id, credits_count, status 
                FROM credit_purchase_records 
                WHERE id = :purchase_id
            """)
            
            result = db.execute(query, {"purchase_id": purchase_id}).fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="购买记录不存在")
            
            user_id, credits_count, status = result
            
            if status == 'paid':
                return {"status": "already_confirmed", "message": "已经确认过"}
            
            if status != 'pending':
                raise HTTPException(status_code=400, detail=f"购买记录状态异常: {status}")
            
            # 更新购买记录状态
            update_purchase_query = text("""
                UPDATE credit_purchase_records 
                SET status = 'paid'
                WHERE id = :purchase_id
            """)
            
            db.execute(update_purchase_query, {"purchase_id": purchase_id})
            
            # 增加用户Credits
            await self._add_user_credits(user_id, credits_count, db)
            
            db.commit()
            
            logger.info(f"用户 {user_id} Credits购买确认成功，增加 {credits_count} Credits")
            
            return {
                "status": "confirmed",
                "user_id": user_id,
                "credits_added": credits_count,
                "purchase_id": purchase_id
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"确认Credits购买失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"确认购买失败: {str(e)}")
    
    async def _add_user_credits(self, user_id: str, credits_count: int, db: Session):
        """
        增加用户Credits
        
        Args:
            user_id: 用户ID
            credits_count: 增加数量
            db: 数据库会话
        """
        update_query = text("""
            UPDATE user_credits 
            SET 
                credits_remaining = credits_remaining + :credits,
                credits_purchased = credits_purchased + :credits,
                updated_at = NOW()
            WHERE user_id = :user_id
        """)
        
        db.execute(update_query, {
            "user_id": user_id,
            "credits": credits_count
        })
    
    async def _record_credits_usage(self, user_id: UUID, credits_used: int, usage_type: str, db: Session):
        """
        记录Credits使用记录
        
        Args:
            user_id: 用户ID
            credits_used: 使用数量
            usage_type: 使用类型
            db: 数据库会话
        """
        try:
            # 这里可以创建一个使用记录表，暂时记录到日志
            logger.info(f"Credits使用记录: 用户={user_id}, 数量={credits_used}, 类型={usage_type}")
            
            # 如果需要详细记录，可以创建 credit_usage_records 表
            # insert_query = text("""
            #     INSERT INTO credit_usage_records (
            #         user_id, credits_used, usage_type, created_at
            #     ) VALUES (
            #         :user_id, :credits_used, :usage_type, NOW()
            #     )
            # """)
            # 
            # db.execute(insert_query, {
            #     "user_id": str(user_id),
            #     "credits_used": credits_used,
            #     "usage_type": usage_type
            # })
            
        except Exception as e:
            logger.error(f"记录Credits使用失败: {str(e)}")
    
    async def get_credits_usage_history(self, user_id: UUID, page: int = 1, size: int = 20, db: Session = None) -> Dict[str, Any]:
        """
        获取Credits使用历史
        
        Args:
            user_id: 用户ID
            page: 页码
            size: 页大小
            db: 数据库会话
            
        Returns:
            使用历史
        """
        try:
            # 暂时返回模拟数据，实际应该从 credit_usage_records 表查询
            return {
                "items": [
                    {
                        "id": "usage_1",
                        "credits_used": 1,
                        "usage_type": "batch_upload",
                        "description": "批量上传任务",
                        "created_at": datetime.now().isoformat()
                    }
                ],
                "total": 1,
                "page": page,
                "size": size,
                "pages": 1
            }
            
        except Exception as e:
            logger.error(f"获取Credits使用历史失败: {str(e)}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "pages": 0
            }
    
    async def get_credits_purchase_history(self, user_id: UUID, page: int = 1, size: int = 20, db: Session = None) -> Dict[str, Any]:
        """
        获取Credits购买历史
        
        Args:
            user_id: 用户ID
            page: 页码
            size: 页大小
            db: 数据库会话
            
        Returns:
            购买历史
        """
        try:
            offset = (page - 1) * size
            
            query = text("""
                SELECT 
                    id, credits_count, unit_price, total_amount,
                    status, created_at
                FROM credit_purchase_records 
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :size OFFSET :offset
            """)
            
            count_query = text("""
                SELECT COUNT(*) FROM credit_purchase_records 
                WHERE user_id = :user_id
            """)
            
            results = db.execute(query, {
                "user_id": str(user_id),
                "size": size,
                "offset": offset
            }).fetchall()
            
            total = db.execute(count_query, {"user_id": str(user_id)}).scalar()
            
            items = []
            for row in results:
                items.append({
                    "id": row[0],
                    "credits_count": row[1],
                    "unit_price": float(row[2]),
                    "total_amount": float(row[3]),
                    "status": row[4],
                    "created_at": row[5].isoformat() if row[5] else None
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"获取Credits购买历史失败: {str(e)}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "pages": 0
            }
    
    async def weekly_credits_reset_batch(self, db: Session) -> Dict[str, Any]:
        """
        批量重置所有用户的每周Credits（定时任务）
        
        Args:
            db: 数据库会话
            
        Returns:
            重置结果
        """
        try:
            # 获取需要重置的用户
            today = date.today()
            
            # 计算本周一
            days_since_monday = today.weekday()
            this_monday = today - timedelta(days=days_since_monday)
            
            query = text("""
                SELECT user_id, last_reset_date 
                FROM user_credits 
                WHERE last_reset_date < :this_monday
            """)
            
            users_to_reset = db.execute(query, {"this_monday": this_monday}).fetchall()
            
            reset_count = 0
            
            for user_id, last_reset in users_to_reset:
                try:
                    await self._reset_user_credits(UUID(user_id), db)
                    reset_count += 1
                except Exception as e:
                    logger.error(f"重置用户 {user_id} Credits失败: {str(e)}")
            
            logger.info(f"批量重置Credits完成，共重置 {reset_count} 个用户")
            
            return {
                "status": "completed",
                "reset_count": reset_count,
                "total_users": len(users_to_reset),
                "reset_date": today.isoformat()
            }
            
        except Exception as e:
            logger.error(f"批量重置Credits失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"批量重置失败: {str(e)}")
    
    async def _log_audit_trail(
        self, 
        user_id: UUID, 
        action: str, 
        credits_amount: int, 
        context: Dict[str, Any], 
        db: Session
    ):
        """记录审计日志"""
        try:
            audit_log = {
                'timestamp': datetime.now().isoformat(),
                'user_id': str(user_id),
                'action': action,
                'credits_change': credits_amount,
                'context': context,
                'ip_address': context.get('ip_address'),
                'user_agent': context.get('user_agent'),
                'session_id': context.get('session_id')
            }
            
            # 记录到安全日志
            logger.info(f"AUDIT: User credits change - {json.dumps(audit_log)}")
            
            # 可以扩展到专门的审计日志表
            # audit_record = UserCreditsAuditLog(**audit_log)
            # db.add(audit_record)
            # db.commit()
            
        except Exception as e:
            logger.error(f"Error logging audit trail: {e}")
            # 审计日志失败不应该影响主要业务流程


# 服务实例工厂函数
def create_user_credits_service(config_service: SystemConfigService = None, payment_service: WeChatPayService = None) -> UserCreditsService:
    """创建用户Credits服务实例"""
    return UserCreditsService(config_service, payment_service)