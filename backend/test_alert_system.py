"""
告警系统测试
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.services.alert_manager import AlertManager, AlertData, AlertSeverity, AlertStatus
from app.services.notification_channels import EmailNotifier, SMSNotifier, WebSocketNotifier


class TestAlertManager:
    """告警管理器测试"""
    
    @pytest.fixture
    async def alert_manager(self):
        """创建告警管理器实例"""
        manager = AlertManager()
        # 模拟初始化
        manager.redis_client = Mock()
        manager.notification_channels = []
        return manager
    
    @pytest.fixture
    def sample_alert_data(self):
        """示例告警数据"""
        return {
            "alertname": "HighErrorRate",
            "status": "firing",
            "labels": {
                "severity": "critical",
                "service": "lawsker-api",
                "instance": "api-server-1"
            },
            "annotations": {
                "summary": "系统错误率过高",
                "description": "过去5分钟内错误率为 15%，超过10%阈值",
                "runbook_url": "https://docs.lawsker.com/runbooks/high-error-rate"
            }
        }
    
    async def test_parse_alert_data(self, alert_manager, sample_alert_data):
        """测试告警数据解析"""
        alert = alert_manager._parse_alert_data(sample_alert_data)
        
        assert alert.name == "HighErrorRate"
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.status == AlertStatus.FIRING
        assert alert.service == "lawsker-api"
        assert alert.message == "系统错误率过高"
        assert alert.runbook_url == "https://docs.lawsker.com/runbooks/high-error-rate"
    
    async def test_is_duplicate_alert(self, alert_manager, sample_alert_data):
        """测试重复告警检测"""
        alert = alert_manager._parse_alert_data(sample_alert_data)
        
        # 第一次不是重复告警
        is_duplicate = await alert_manager._is_duplicate_alert(alert)
        assert not is_duplicate
        
        # 添加到活跃告警
        alert_manager.active_alerts[alert.alert_id] = alert
        
        # 相同告警应该被识别为重复
        new_alert = alert_manager._parse_alert_data(sample_alert_data)
        is_duplicate = await alert_manager._is_duplicate_alert(new_alert)
        assert is_duplicate
    
    async def test_process_alert(self, alert_manager, sample_alert_data):
        """测试告警处理"""
        # 模拟通知渠道
        mock_notifier = Mock()
        mock_notifier.send_notification = AsyncMock(return_value=True)
        alert_manager.notification_channels = [mock_notifier]
        
        # 模拟Redis操作
        alert_manager.redis_client.setex = AsyncMock()
        
        # 处理告警
        result = await alert_manager.process_alert(sample_alert_data)
        
        assert result is True
        assert len(alert_manager.active_alerts) == 1
        mock_notifier.send_notification.assert_called_once()
    
    async def test_silence_alert(self, alert_manager, sample_alert_data):
        """测试告警静默"""
        # 先添加一个活跃告警
        alert = alert_manager._parse_alert_data(sample_alert_data)
        alert_manager.active_alerts[alert.alert_id] = alert
        
        # 模拟Redis操作
        alert_manager.redis_client.setex = AsyncMock()
        
        # 静默告警
        result = await alert_manager.silence_alert(alert.alert_id, 60)
        
        assert result is True
        assert alert_manager.active_alerts[alert.alert_id].status == AlertStatus.SILENCED
        alert_manager.redis_client.setex.assert_called_once()
    
    async def test_resolve_alert(self, alert_manager, sample_alert_data):
        """测试告警解决"""
        # 先添加一个活跃告警
        alert = alert_manager._parse_alert_data(sample_alert_data)
        alert_manager.active_alerts[alert.alert_id] = alert
        
        # 模拟Redis操作
        alert_manager.redis_client.delete = AsyncMock()
        
        # 解决告警
        result = await alert_manager.resolve_alert(alert.alert_id)
        
        assert result is True
        assert alert.alert_id not in alert_manager.active_alerts
        alert_manager.redis_client.delete.assert_called_once()


class TestNotificationChannels:
    """通知渠道测试"""
    
    @pytest.fixture
    def sample_alert(self):
        """示例告警数据"""
        return AlertData(
            alert_id="test_alert_1",
            name="HighErrorRate",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.FIRING,
            message="系统错误率过高",
            description="过去5分钟内错误率为 15%，超过10%阈值",
            service="lawsker-api",
            timestamp=datetime.now(),
            labels={"severity": "critical", "service": "lawsker-api"},
            annotations={"summary": "系统错误率过高"},
            runbook_url="https://docs.lawsker.com/runbooks/high-error-rate"
        )
    
    async def test_email_notifier(self, sample_alert):
        """测试邮件通知器"""
        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="password",
            from_email="alerts@lawsker.com"
        )
        
        # 模拟获取收件人
        notifier._get_recipients = AsyncMock(return_value=["admin@lawsker.com"])
        
        # 模拟发送邮件
        notifier._send_email = AsyncMock()
        
        result = await notifier.send_notification(sample_alert)
        
        assert result is True
        notifier._get_recipients.assert_called_once_with(sample_alert.severity)
        notifier._send_email.assert_called_once()
    
    async def test_sms_notifier(self, sample_alert):
        """测试短信通知器"""
        notifier = SMSNotifier(
            api_url="https://sms.example.com/send",
            api_key="test_api_key"
        )
        
        # 模拟获取收件人
        notifier._get_sms_recipients = AsyncMock(return_value=["13800138000"])
        
        # 模拟发送短信
        notifier._send_sms = AsyncMock()
        
        result = await notifier.send_notification(sample_alert)
        
        assert result is True
        notifier._send_sms.assert_called_once()
    
    async def test_websocket_notifier(self, sample_alert):
        """测试WebSocket通知器"""
        notifier = WebSocketNotifier()
        
        # 模拟WebSocket管理器
        with patch('app.services.notification_channels.websocket_manager') as mock_ws:
            mock_ws.broadcast_to_admins = AsyncMock()
            
            result = await notifier.send_notification(sample_alert)
            
            assert result is True
            mock_ws.broadcast_to_admins.assert_called_once()


class TestAlertIntegration:
    """告警系统集成测试"""
    
    async def test_full_alert_workflow(self):
        """测试完整的告警工作流"""
        # 创建告警管理器
        manager = AlertManager()
        manager.redis_client = Mock()
        
        # 创建模拟通知渠道
        mock_email = Mock()
        mock_email.send_notification = AsyncMock(return_value=True)
        mock_websocket = Mock()
        mock_websocket.send_notification = AsyncMock(return_value=True)
        
        manager.notification_channels = [mock_email, mock_websocket]
        
        # 模拟Redis操作
        manager.redis_client.setex = AsyncMock()
        manager.redis_client.delete = AsyncMock()
        
        # 告警数据
        alert_data = {
            "alertname": "HighErrorRate",
            "status": "firing",
            "labels": {
                "severity": "critical",
                "service": "lawsker-api"
            },
            "annotations": {
                "summary": "系统错误率过高",
                "description": "错误率超过阈值"
            }
        }
        
        # 1. 处理告警
        result = await manager.process_alert(alert_data)
        assert result is True
        assert len(manager.active_alerts) == 1
        
        # 2. 验证通知发送
        mock_email.send_notification.assert_called_once()
        mock_websocket.send_notification.assert_called_once()
        
        # 3. 静默告警
        alert_id = list(manager.active_alerts.keys())[0]
        silence_result = await manager.silence_alert(alert_id, 60)
        assert silence_result is True
        
        # 4. 解决告警
        resolve_result = await manager.resolve_alert(alert_id)
        assert resolve_result is True
        assert len(manager.active_alerts) == 0


async def test_alert_deduplication():
    """测试告警去重功能"""
    manager = AlertManager()
    manager.redis_client = Mock()
    manager.notification_channels = []
    
    alert_data = {
        "alertname": "TestAlert",
        "status": "firing",
        "labels": {"severity": "warning", "service": "test"},
        "annotations": {"summary": "测试告警"}
    }
    
    # 第一次处理告警
    result1 = await manager.process_alert(alert_data)
    assert result1 is True
    assert len(manager.active_alerts) == 1
    
    # 立即再次处理相同告警（应该被去重）
    result2 = await manager.process_alert(alert_data)
    assert result2 is False  # 被去重，返回False
    assert len(manager.active_alerts) == 1  # 数量不变


async def test_alert_escalation():
    """测试告警升级"""
    manager = AlertManager()
    manager.redis_client = Mock()
    
    # 创建不同级别的通知渠道
    email_notifier = Mock()
    email_notifier.send_notification = AsyncMock(return_value=True)
    sms_notifier = Mock()
    sms_notifier.send_notification = AsyncMock(return_value=True)
    
    manager.notification_channels = [email_notifier, sms_notifier]
    
    # 警告级别告警
    warning_alert = {
        "alertname": "WarningAlert",
        "status": "firing",
        "labels": {"severity": "warning", "service": "test"},
        "annotations": {"summary": "警告告警"}
    }
    
    # 严重级别告警
    critical_alert = {
        "alertname": "CriticalAlert",
        "status": "firing",
        "labels": {"severity": "critical", "service": "test"},
        "annotations": {"summary": "严重告警"}
    }
    
    # 处理警告告警（应该只发送邮件）
    await manager.process_alert(warning_alert)
    
    # 处理严重告警（应该发送邮件和短信）
    await manager.process_alert(critical_alert)
    
    # 验证通知发送次数
    assert email_notifier.send_notification.call_count == 2
    # 注意：这里的逻辑需要根据实际的通知渠道选择逻辑来调整


if __name__ == "__main__":
    # 运行基本测试
    async def run_tests():
        print("开始告警系统测试...")
        
        # 测试告警管理器
        manager = AlertManager()
        manager.redis_client = Mock()
        manager.notification_channels = []
        
        # 测试数据
        test_alert = {
            "alertname": "TestAlert",
            "status": "firing",
            "labels": {
                "severity": "critical",
                "service": "lawsker-api"
            },
            "annotations": {
                "summary": "测试告警",
                "description": "这是一个测试告警"
            }
        }
        
        # 处理告警
        result = await manager.process_alert(test_alert)
        print(f"告警处理结果: {result}")
        print(f"活跃告警数量: {len(manager.active_alerts)}")
        
        # 获取活跃告警
        active_alerts = await manager.get_active_alerts()
        print(f"活跃告警列表: {[alert.name for alert in active_alerts]}")
        
        print("告警系统测试完成!")
    
    asyncio.run(run_tests())