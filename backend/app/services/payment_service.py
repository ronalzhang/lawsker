"""
微信支付服务模块
实现微信支付集成和30秒实时分账功能
"""

import hashlib
import time
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import UUID

import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.config_service import SystemConfigService
from app.core.database import get_db
from app.models.finance import Transaction, CommissionSplit, PaymentOrder, Wallet, WithdrawalRequest, TransactionType, TransactionStatus, CommissionStatus, WithdrawalStatus
from app.models.case import Case
from app.models.user import User

logger = logging.getLogger(__name__)


class WeChatPayError(Exception):
    """微信支付异常"""
    pass


class CommissionSplitError(Exception):
    """分账异常"""
    pass


class WithdrawalError(Exception):
    """提现异常"""
    pass


class WeChatPayService:
    """微信支付服务类"""
    
    def __init__(self, config_service: SystemConfigService):
        self.config_service = config_service
        
    async def _get_wechat_config(self, tenant_id: Optional[UUID] = None) -> Dict[str, Any]:
        """获取微信支付配置"""
        config = await self.config_service.get_config("payment_keys", "wechat_pay", tenant_id)
        if not config or not config.get("enabled"):
            raise WeChatPayError("微信支付未配置或未启用")
        return config
        
    def _generate_sign(self, params: Dict[str, Any], api_key: str) -> str:
        """生成微信支付签名"""
        # 排序参数
        sorted_params = sorted(params.items())
        
        # 拼接参数字符串
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params if v])
        param_str += f"&key={api_key}"
        
        # MD5签名
        sign = hashlib.md5(param_str.encode('utf-8')).hexdigest().upper()
        return sign
    
    def _generate_nonce_str(self) -> str:
        """生成随机字符串"""
        return str(uuid.uuid4()).replace('-', '')
    
    async def create_payment_order(
        self,
        case_id: UUID,
        amount: Decimal,
        description: str,
        user_id: UUID,
        db: Session,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        创建微信支付订单
        
        Args:
            case_id: 案件ID
            amount: 支付金额（元）
            description: 支付描述
            user_id: 用户ID
            db: 数据库会话
            tenant_id: 租户ID
            
        Returns:
            包含支付信息的字典
        """
        try:
            # 获取微信支付配置
            config = await self._get_wechat_config(tenant_id)
            
            # 检查案件是否存在
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail="案件不存在")
            
            # 创建支付订单记录
            order_no = f"LW{int(time.time())}{str(case_id)[-6:]}"
            payment_order = PaymentOrder(
                order_no=order_no,
                case_id=case_id,
                user_id=user_id,
                amount=amount,
                description=description,
                status="pending",
                expires_at=datetime.now() + timedelta(minutes=30)
            )
            db.add(payment_order)
            db.commit()
            
            # 构建微信支付参数
            params = {
                "appid": config["app_id"],
                "mch_id": config["mch_id"],
                "nonce_str": self._generate_nonce_str(),
                "body": description,
                "out_trade_no": order_no,
                "total_fee": int(amount * 100),  # 转换为分
                "spbill_create_ip": "127.0.0.1",
                "notify_url": config.get("notify_url", "https://api.lawsker.com/api/v1/finance/payment/callback"),
                "trade_type": "NATIVE",  # 扫码支付
                "profit_sharing": "Y"  # 开启分账
            }
            
            # 生成签名
            params["sign"] = self._generate_sign(params, config["api_key"])
            
            # 构建XML请求体
            xml_data = self._dict_to_xml(params)
            
            # 调用微信支付API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.mch.weixin.qq.com/pay/unifiedorder",
                    content=xml_data,
                    headers={"Content-Type": "application/xml"}
                )
            
            # 解析响应
            result = self._xml_to_dict(response.text)
            
            if result.get("return_code") != "SUCCESS":
                raise WeChatPayError(f"微信支付请求失败: {result.get('return_msg')}")
            
            if result.get("result_code") != "SUCCESS":
                raise WeChatPayError(f"微信支付业务失败: {result.get('err_code_des')}")
            
            # 更新订单状态
            payment_order.prepay_id = result.get("prepay_id")
            payment_order.code_url = result.get("code_url")
            db.commit()
            
            return {
                "order_no": order_no,
                "qr_code": result.get("code_url"),
                "amount": float(amount),
                "description": description,
                "expires_at": payment_order.expires_at.isoformat() if payment_order.expires_at else None
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建支付订单失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"创建支付订单失败: {str(e)}")
    
    async def handle_payment_callback(
        self, 
        xml_data: str, 
        db: Session,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        处理微信支付回调
        
        Args:
            xml_data: 微信支付回调XML数据
            db: 数据库会话
            tenant_id: 租户ID
            
        Returns:
            处理结果
        """
        try:
            # 获取微信支付配置
            config = await self._get_wechat_config(tenant_id)
            
            # 解析回调数据
            callback_data = self._xml_to_dict(xml_data)
            
            # 验证签名
            sign = callback_data.pop("sign", "")
            if sign != self._generate_sign(callback_data, config["api_key"]):
                raise WeChatPayError("签名验证失败")
            
            order_no = callback_data.get("out_trade_no")
            transaction_id = callback_data.get("transaction_id")
            total_fee = int(callback_data.get("total_fee", 0)) / 100  # 转换为元
            
            # 查找订单
            payment_order = db.query(PaymentOrder).filter(
                PaymentOrder.order_no == order_no
            ).first()
            
            if not payment_order:
                raise WeChatPayError("订单不存在")
            
            if payment_order.status == "paid":
                return {"status": "success", "message": "订单已处理"}
            
            # 更新订单状态
            payment_order.status = "paid"
            payment_order.transaction_id = transaction_id
            payment_order.paid_at = datetime.now()
            
            # 创建交易记录
            transaction = Transaction(
                case_id=payment_order.case_id,
                amount=Decimal(str(total_fee)),
                transaction_type=TransactionType.PAYMENT,
                payment_gateway="wechat",
                gateway_txn_id=transaction_id,
                status=TransactionStatus.COMPLETED,
                description=f"微信支付订单: {order_no}",
                completed_at=datetime.now(),
                gateway_response=callback_data
            )
            db.add(transaction)
            db.commit()
            
            # 触发30秒实时分账
            await self._trigger_commission_split(transaction.id, db, tenant_id)
            
            return {"status": "success", "message": "支付成功"}
            
        except Exception as e:
            db.rollback()
            logger.error(f"处理支付回调失败: {str(e)}")
            raise WeChatPayError(f"处理支付回调失败: {str(e)}")
    
    async def _trigger_commission_split(
        self, 
        transaction_id: UUID, 
        db: Session,
        tenant_id: Optional[UUID] = None
    ):
        """
        触发30秒实时分账
        
        Args:
            transaction_id: 交易ID
            db: 数据库会话
            tenant_id: 租户ID
        """
        try:
            # 获取交易信息
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
            
            if not transaction:
                raise CommissionSplitError("交易不存在")
            
            # 获取案件信息
            case = db.query(Case).filter(Case.id == transaction.case_id).first()
            if not case:
                raise CommissionSplitError("案件不存在")
            
            # 获取分成配置
            commission_config = await self.config_service.get_config("business", "commission_rates", tenant_id)
            if not commission_config:
                # 使用默认配置
                commission_config = {
                    "lawyer": 0.30,
                    "sales": 0.20,
                    "platform": 0.50,
                    "safety_margin": 0.15
                }
            
            # 计算分成金额（扣除安全边际）
            safety_margin = Decimal(str(commission_config.get('safety_margin', 0.15)))
            available_amount = transaction.amount * (Decimal('1') - safety_margin)
            
            lawyer_rate = Decimal(str(commission_config.get('lawyer', 0.30)))
            sales_rate = Decimal(str(commission_config.get('sales', 0.20)))
            platform_rate = Decimal(str(commission_config.get('platform', 0.50)))
            
            lawyer_amount = available_amount * lawyer_rate
            sales_amount = available_amount * sales_rate
            platform_amount = available_amount * platform_rate
            
            commission_splits = []
            
            # 律师分成
            if case.assigned_to_user_id and lawyer_amount > 0:
                lawyer_user = db.query(User).filter(User.id == case.assigned_to_user_id).first()
                if lawyer_user:
                    lawyer_split = CommissionSplit(
                        transaction_id=transaction_id,
                        user_id=lawyer_user.id,
                        role_at_split="lawyer",
                        amount=lawyer_amount,
                        percentage=lawyer_rate,
                        status=CommissionStatus.PENDING
                    )
                    commission_splits.append(lawyer_split)
                    
                    # 更新律师钱包
                    await self._update_wallet(lawyer_user.id, lawyer_amount, "commission", db)
            
            # 销售分成
            if hasattr(case, 'sales_user_id') and case.sales_user_id and sales_amount > 0:
                sales_user = db.query(User).filter(User.id == case.sales_user_id).first()
                if sales_user:
                    sales_split = CommissionSplit(
                        transaction_id=transaction_id,
                        user_id=sales_user.id,
                        role_at_split="sales",
                        amount=sales_amount,
                        percentage=sales_rate,
                        status=CommissionStatus.PENDING
                    )
                    commission_splits.append(sales_split)
                    
                    # 更新销售钱包
                    await self._update_wallet(sales_user.id, sales_amount, "commission", db)
            
            # 平台分成（记录但不创建钱包）
            platform_split = CommissionSplit(
                transaction_id=transaction_id,
                user_id=None,  # 平台收益
                role_at_split="platform",
                amount=platform_amount,
                percentage=platform_rate,
                status=CommissionStatus.PAID  # 平台直接收取
            )
            commission_splits.append(platform_split)
            
            # 批量保存分成记录
            db.add_all(commission_splits)
            db.commit()
            
            logger.info(f"交易 {transaction_id} 分账完成: "
                       f"律师 {lawyer_amount}, 销售 {sales_amount}, 平台 {platform_amount}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"分账处理失败: {str(e)}")
            raise CommissionSplitError(f"分账处理失败: {str(e)}")
    
    async def _update_wallet(
        self, 
        user_id: UUID, 
        amount: Decimal, 
        transaction_type: str, 
        db: Session
    ):
        """
        更新用户钱包余额
        
        Args:
            user_id: 用户ID
            amount: 金额
            transaction_type: 交易类型
            db: 数据库会话
        """
        try:
            # 获取或创建钱包
            wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
            if not wallet:
                wallet = Wallet(
                    user_id=user_id,
                    balance=Decimal('0'),
                    withdrawable_balance=Decimal('0'),
                    frozen_balance=Decimal('0'),
                    total_earned=Decimal('0'),
                    total_withdrawn=Decimal('0'),
                    commission_count=0
                )
                db.add(wallet)
            
            # 更新余额
            wallet.balance += amount
            wallet.withdrawable_balance += amount
            wallet.total_earned += amount
            wallet.commission_count += 1
            
            if transaction_type == "commission":
                wallet.last_commission_at = datetime.now()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"更新钱包失败: {str(e)}")
            raise
    
    def _dict_to_xml(self, params: Dict[str, Any]) -> str:
        """字典转XML"""
        xml_items = [f"<{k}><![CDATA[{v}]]></{k}>" for k, v in params.items()]
        return f"<xml>{''.join(xml_items)}</xml>"
    
    def _xml_to_dict(self, xml_str: str) -> Dict[str, str]:
        """XML转字典（简单实现）"""
        import re
        result = {}
        pattern = r'<(\w+)><!\[CDATA\[(.*?)\]\]></\1>|<(\w+)>(.*?)</\3>'
        matches = re.findall(pattern, xml_str)
        
        for match in matches:
            if match[0]:  # CDATA格式
                result[match[0]] = match[1]
            else:  # 普通格式
                result[match[2]] = match[3]
        
        return result


class CommissionSplitService:
    """分账服务类"""
    
    def __init__(self, config_service: SystemConfigService):
        self.config_service = config_service
    
    def get_commission_summary(self, user_id: UUID, db: Session) -> Dict[str, Any]:
        """
        获取用户分成汇总
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            分成汇总信息
        """
        try:
            # 查询用户分成记录
            splits = db.query(CommissionSplit).filter(
                CommissionSplit.user_id == user_id,
                CommissionSplit.status == CommissionStatus.PAID
            ).all()
            
            total_amount = sum(split.amount for split in splits)
            split_count = len(splits)
            
            # 按角色分组统计
            role_stats = {}
            for split in splits:
                role = split.role_at_split
                if role not in role_stats:
                    role_stats[role] = {"count": 0, "amount": Decimal('0')}
                role_stats[role]["count"] += 1
                role_stats[role]["amount"] += split.amount
            
            # 最近30天统计
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_splits = [s for s in splits if s.paid_at and s.paid_at >= thirty_days_ago]
            recent_amount = sum(split.amount for split in recent_splits)
            
            return {
                "total_amount": float(total_amount),
                "split_count": split_count,
                "recent_30_days_amount": float(recent_amount),
                "role_statistics": {
                    role: {
                        "count": stats["count"],
                        "amount": float(stats["amount"])
                    }
                    for role, stats in role_stats.items()
                },
                "average_amount": float(total_amount / split_count) if split_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取分成汇总失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取分成汇总失败: {str(e)}")
    
    def get_commission_details(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        获取用户分成明细
        
        Args:
            user_id: 用户ID
            page: 页码
            size: 页大小
            db: 数据库会话
            
        Returns:
            分成明细列表
        """
        try:
            # 查询分成记录
            query = db.query(CommissionSplit).filter(
                CommissionSplit.user_id == user_id
            ).order_by(CommissionSplit.created_at.desc())
            
            total = query.count()
            splits = query.offset((page - 1) * size).limit(size).all()
            
            items = []
            for split in splits:
                # 获取关联交易信息
                transaction = db.query(Transaction).filter(
                    Transaction.id == split.transaction_id
                ).first()
                
                case_info = {}
                if transaction and transaction.case_id:
                    case = db.query(Case).filter(Case.id == transaction.case_id).first()
                    if case:
                        case_info = {
                            "case_id": str(case.id),
                            "case_number": getattr(case, 'case_number', ''),
                            "debtor_name": getattr(case, 'debtor_name', '')
                        }
                
                items.append({
                    "id": str(split.id),
                    "amount": float(split.amount),
                    "percentage": float(split.percentage),
                    "role": split.role_at_split,
                    "status": split.status.value,
                    "created_at": split.created_at.isoformat(),
                    "paid_at": split.paid_at.isoformat() if split.paid_at else None,
                    "case_info": case_info
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"获取分成明细失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取分成明细失败: {str(e)}")


class WithdrawalService:
    """提现服务类"""
    
    def __init__(self, config_service: SystemConfigService):
        self.config_service = config_service
    
    async def create_withdrawal_request(
        self,
        user_id: UUID,
        amount: Decimal,
        bank_account: str,
        bank_name: str,
        account_holder: str,
        db: Session,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        创建提现申请
        
        Args:
            user_id: 用户ID
            amount: 提现金额
            bank_account: 银行账户
            bank_name: 银行名称
            account_holder: 账户姓名
            db: 数据库会话
            tenant_id: 租户ID
            
        Returns:
            提现申请信息
        """
        try:
            # 获取用户钱包
            wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
            if not wallet:
                raise WithdrawalError("钱包不存在")
            
            # 获取提现配置
            withdrawal_config = await self.config_service.get_config("business", "withdrawal_settings", tenant_id)
            if not withdrawal_config:
                withdrawal_config = {
                    "min_amount": 10.0,
                    "max_amount": 50000.0,
                    "daily_limit": 100000.0,
                    "fee_rate": 0.001,
                    "min_fee": 1.0,
                    "max_fee": 50.0,
                    "auto_approve_threshold": 1000.0
                }
            
            min_amount = Decimal(str(withdrawal_config.get("min_amount", 10.0)))
            max_amount = Decimal(str(withdrawal_config.get("max_amount", 50000.0)))
            daily_limit = Decimal(str(withdrawal_config.get("daily_limit", 100000.0)))
            
            # 验证金额
            if amount < min_amount:
                raise WithdrawalError(f"提现金额不能少于{min_amount}元")
            
            if amount > max_amount:
                raise WithdrawalError(f"单次提现金额不能超过{max_amount}元")
            
            if amount > wallet.withdrawable_balance:
                raise WithdrawalError("可提现余额不足")
            
            # 检查日限额
            today = datetime.now().date()
            today_withdrawals = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.user_id == user_id,
                WithdrawalRequest.created_at >= today,
                WithdrawalRequest.status.in_([WithdrawalStatus.PENDING, WithdrawalStatus.APPROVED, WithdrawalStatus.PROCESSING, WithdrawalStatus.COMPLETED])
            ).all()
            
            today_total = sum(w.amount for w in today_withdrawals)
            if today_total + amount > daily_limit:
                raise WithdrawalError(f"超过每日提现限额{daily_limit}元")
            
            # 计算手续费
            fee_rate = Decimal(str(withdrawal_config.get("fee_rate", 0.001)))
            min_fee = Decimal(str(withdrawal_config.get("min_fee", 1.0)))
            max_fee = Decimal(str(withdrawal_config.get("max_fee", 50.0)))
            
            fee = max(min_fee, min(amount * fee_rate, max_fee))
            actual_amount = amount - fee
            
            # 生成申请单号
            request_number = f"WD{int(time.time())}{str(user_id)[-6:]}"
            
            # 风险评估
            risk_score = await self._calculate_risk_score(user_id, amount, db)
            auto_approve_threshold = Decimal(str(withdrawal_config.get("auto_approve_threshold", 1000.0)))
            auto_approved = amount <= auto_approve_threshold and risk_score < 30
            require_manual_review = risk_score >= 70
            
            # 创建提现申请
            withdrawal_request = WithdrawalRequest(
                user_id=user_id,
                wallet_id=user_id,  # wallet的主键就是user_id
                request_number=request_number,
                amount=amount,
                fee=fee,
                actual_amount=actual_amount,
                bank_account=bank_account,
                bank_name=bank_name,
                account_holder=account_holder,
                status=WithdrawalStatus.APPROVED if auto_approved else WithdrawalStatus.PENDING,
                risk_score=risk_score,
                auto_approved=auto_approved,
                require_manual_review=require_manual_review
            )
            
            db.add(withdrawal_request)
            
            # 冻结相应金额
            wallet.withdrawable_balance -= amount
            wallet.frozen_balance += amount
            
            db.commit()
            
            # 如果自动审批，立即处理
            if auto_approved:
                await self._process_withdrawal(withdrawal_request.id, db, auto_process=True)
            
            return {
                "id": str(withdrawal_request.id),
                "request_number": request_number,
                "amount": float(amount),
                "fee": float(fee),
                "actual_amount": float(actual_amount),
                "status": withdrawal_request.status.value,
                "auto_approved": auto_approved,
                "estimated_arrival": "1-3个工作日" if not auto_approved else "24小时内"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建提现申请失败: {str(e)}")
            raise WithdrawalError(f"创建提现申请失败: {str(e)}")
    
    async def get_withdrawal_requests(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[WithdrawalStatus] = None,
        page: int = 1,
        size: int = 20,
        db: Session = None
    ) -> Dict[str, Any]:
        """获取提现申请列表"""
        try:
            query = db.query(WithdrawalRequest)
            
            if user_id:
                query = query.filter(WithdrawalRequest.user_id == user_id)
            
            if status:
                query = query.filter(WithdrawalRequest.status == status)
            
            query = query.order_by(WithdrawalRequest.created_at.desc())
            
            total = query.count()
            requests = query.offset((page - 1) * size).limit(size).all()
            
            items = []
            for req in requests:
                user = db.query(User).filter(User.id == req.user_id).first()
                items.append({
                    "id": str(req.id),
                    "request_number": req.request_number,
                    "user_id": str(req.user_id),
                    "user_name": user.username if user else "未知用户",
                    "amount": float(req.amount),
                    "fee": float(req.fee),
                    "actual_amount": float(req.actual_amount),
                    "bank_account": req.bank_account,
                    "bank_name": req.bank_name,
                    "account_holder": req.account_holder,
                    "status": req.status.value,
                    "risk_score": float(req.risk_score) if req.risk_score else None,
                    "auto_approved": req.auto_approved,
                    "admin_notes": req.admin_notes,
                    "created_at": req.created_at.isoformat(),
                    "processed_at": req.processed_at.isoformat() if req.processed_at else None
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"获取提现申请列表失败: {str(e)}")
            raise WithdrawalError(f"获取提现申请列表失败: {str(e)}")
    
    async def approve_withdrawal(
        self,
        withdrawal_id: UUID,
        admin_id: UUID,
        admin_notes: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """审批通过提现申请"""
        try:
            withdrawal = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.id == withdrawal_id
            ).first()
            
            if not withdrawal:
                raise WithdrawalError("提现申请不存在")
            
            if withdrawal.status != WithdrawalStatus.PENDING:
                raise WithdrawalError("该申请已处理，不能重复操作")
            
            withdrawal.status = WithdrawalStatus.APPROVED
            withdrawal.processed_by = admin_id
            withdrawal.processed_at = datetime.now()
            if admin_notes:
                withdrawal.admin_notes = admin_notes
            
            db.commit()
            
            # 异步处理实际转账
            await self._process_withdrawal(withdrawal_id, db)
            
            return {
                "success": True,
                "message": "提现申请已审批通过",
                "withdrawal_id": str(withdrawal_id)
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"审批提现申请失败: {str(e)}")
            raise WithdrawalError(f"审批提现申请失败: {str(e)}")
    
    async def reject_withdrawal(
        self,
        withdrawal_id: UUID,
        admin_id: UUID,
        admin_notes: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """拒绝提现申请"""
        try:
            withdrawal = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.id == withdrawal_id
            ).first()
            
            if not withdrawal:
                raise WithdrawalError("提现申请不存在")
            
            if withdrawal.status != WithdrawalStatus.PENDING:
                raise WithdrawalError("该申请已处理，不能重复操作")
            
            # 恢复钱包余额
            wallet = db.query(Wallet).filter(Wallet.user_id == withdrawal.user_id).first()
            if wallet:
                wallet.withdrawable_balance += withdrawal.amount
                wallet.frozen_balance -= withdrawal.amount
            
            withdrawal.status = WithdrawalStatus.REJECTED
            withdrawal.processed_by = admin_id
            withdrawal.processed_at = datetime.now()
            withdrawal.admin_notes = admin_notes
            
            db.commit()
            
            return {
                "success": True,
                "message": "提现申请已拒绝",
                "withdrawal_id": str(withdrawal_id)
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"拒绝提现申请失败: {str(e)}")
            raise WithdrawalError(f"拒绝提现申请失败: {str(e)}")
    
    async def _calculate_risk_score(
        self,
        user_id: UUID,
        amount: Decimal,
        db: Session
    ) -> Decimal:
        """计算风险评分"""
        try:
            risk_score = Decimal('0')
            
            # 获取用户历史提现记录
            user_withdrawals = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.user_id == user_id
            ).all()
            
            # 新用户风险
            if len(user_withdrawals) == 0:
                risk_score += Decimal('20')
            
            # 大额提现风险
            if amount > Decimal('10000'):
                risk_score += Decimal('30')
            elif amount > Decimal('5000'):
                risk_score += Decimal('15')
            
            # 频繁提现风险
            recent_withdrawals = [w for w in user_withdrawals 
                                if w.created_at >= datetime.now() - timedelta(days=7)]
            if len(recent_withdrawals) > 3:
                risk_score += Decimal('25')
            
            # 失败记录风险
            failed_withdrawals = [w for w in user_withdrawals 
                                if w.status == WithdrawalStatus.FAILED]
            if len(failed_withdrawals) > 0:
                risk_score += Decimal('15')
            
            return min(risk_score, Decimal('100'))
            
        except Exception as e:
            logger.error(f"计算风险评分失败: {str(e)}")
            return Decimal('50')  # 默认中等风险
    
    async def _process_withdrawal(
        self,
        withdrawal_id: UUID,
        db: Session,
        auto_process: bool = False
    ):
        """处理实际转账"""
        try:
            withdrawal = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.id == withdrawal_id
            ).first()
            
            if not withdrawal:
                return
            
            # 更新状态为处理中
            withdrawal.status = WithdrawalStatus.PROCESSING
            db.commit()
            
            # 这里应该调用实际的银行转账API
            # 目前模拟转账成功
            success = await self._simulate_bank_transfer(withdrawal)
            
            if success:
                # 转账成功
                withdrawal.status = WithdrawalStatus.COMPLETED
                withdrawal.gateway_txn_id = f"TXN{int(time.time())}"
                
                # 更新钱包统计
                wallet = db.query(Wallet).filter(Wallet.user_id == withdrawal.user_id).first()
                if wallet:
                    wallet.frozen_balance -= withdrawal.amount
                    wallet.total_withdrawn += withdrawal.amount
                
            else:
                # 转账失败，恢复余额
                withdrawal.status = WithdrawalStatus.FAILED
                
                wallet = db.query(Wallet).filter(Wallet.user_id == withdrawal.user_id).first()
                if wallet:
                    wallet.withdrawable_balance += withdrawal.amount
                    wallet.frozen_balance -= withdrawal.amount
            
            db.commit()
            
        except Exception as e:
            logger.error(f"处理提现转账失败: {str(e)}")
            # 转账失败，更新状态并恢复余额
            if withdrawal:
                withdrawal.status = WithdrawalStatus.FAILED
                wallet = db.query(Wallet).filter(Wallet.user_id == withdrawal.user_id).first()
                if wallet:
                    wallet.withdrawable_balance += withdrawal.amount
                    wallet.frozen_balance -= withdrawal.amount
                db.commit()
    
    async def _simulate_bank_transfer(self, withdrawal: WithdrawalRequest) -> bool:
        """模拟银行转账（实际应调用银行API）"""
        # 模拟90%成功率
        import random
        return random.random() > 0.1


# 服务实例工厂函数
def create_wechat_pay_service(config_service: SystemConfigService) -> WeChatPayService:
    """创建微信支付服务实例"""
    return WeChatPayService(config_service)


def create_commission_split_service(config_service: SystemConfigService) -> CommissionSplitService:
    """创建分账服务实例"""
    return CommissionSplitService(config_service)


def create_withdrawal_service(config_service: SystemConfigService) -> WithdrawalService:
    """创建提现服务实例"""
    return WithdrawalService(config_service) 