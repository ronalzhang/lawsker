#!/usr/bin/env python3
"""
启动自动化运维服务脚本
初始化健康监控、告警自动化等服务
"""
import asyncio
import signal
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.health_monitor import health_monitor
from app.services.alert_automation import alert_automation
from app.core.logging import get_logger

logger = get_logger(__name__)

class AutomationServiceManager:
    """自动化服务管理器"""
    
    def __init__(self):
        self.services = {
            "health_monitor": health_monitor,
            "alert_automation": alert_automation
        }
        self.running = False
    
    async def start_all_services(self):
        """启动所有服务"""
        logger.info("Starting automation services...")
        
        try:
            # 启动健康监控服务
            logger.info("Starting health monitoring service...")
            await health_monitor.start_monitoring()
            
            # 启动告警自动化服务
            logger.info("Starting alert automation service...")
            await alert_automation.start_processing()
            
            self.running = True
            logger.info("All automation services started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start services: {str(e)}")
            await self.stop_all_services()
            raise
    
    async def stop_all_services(self):
        """停止所有服务"""
        if not self.running:
            return
        
        logger.info("Stopping automation services...")
        
        try:
            # 停止健康监控服务
            logger.info("Stopping health monitoring service...")
            await health_monitor.stop_monitoring()
            
            # 停止告警自动化服务
            logger.info("Stopping alert automation service...")
            await alert_automation.stop_processing()
            
            self.running = False
            logger.info("All automation services stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping services: {str(e)}")
    
    async def get_service_status(self):
        """获取服务状态"""
        return {
            "health_monitor": {
                "running": health_monitor.is_running,
                "checkers_count": len(health_monitor.checkers)
            },
            "alert_automation": {
                "running": alert_automation.is_running,
                "rules_count": len(alert_automation.rules),
                "enabled_rules": len([r for r in alert_automation.rules.values() if r.enabled])
            }
        }
    
    async def restart_service(self, service_name: str):
        """重启指定服务"""
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        logger.info(f"Restarting service: {service_name}")
        
        if service_name == "health_monitor":
            await health_monitor.stop_monitoring()
            await health_monitor.start_monitoring()
        elif service_name == "alert_automation":
            await alert_automation.stop_processing()
            await alert_automation.start_processing()
        
        logger.info(f"Service {service_name} restarted successfully")

async def main():
    """主函数"""
    service_manager = AutomationServiceManager()
    
    # 设置信号处理器
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(service_manager.stop_all_services())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动所有服务
        await service_manager.start_all_services()
        
        # 定期检查服务状态
        while service_manager.running:
            try:
                status = await service_manager.get_service_status()
                logger.debug(f"Service status: {status}")
                
                # 检查服务是否正常运行
                if not status["health_monitor"]["running"]:
                    logger.warning("Health monitor is not running, restarting...")
                    await service_manager.restart_service("health_monitor")
                
                if not status["alert_automation"]["running"]:
                    logger.warning("Alert automation is not running, restarting...")
                    await service_manager.restart_service("alert_automation")
                
                # 等待60秒后再次检查
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in service monitoring loop: {str(e)}")
                await asyncio.sleep(30)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        await service_manager.stop_all_services()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service manager stopped by user")
    except Exception as e:
        logger.error(f"Service manager failed: {str(e)}")
        sys.exit(1)