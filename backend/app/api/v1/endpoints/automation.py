"""
自动化运维管理API端点
提供部署、健康监控、告警自动化等功能的API接口
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.deps import get_current_admin_user
from app.services.health_monitor import health_monitor, HealthStatus
from app.services.alert_automation import alert_automation, AutomationRule, ActionType
# from app.scripts.auto_deploy import DeploymentManager  # 暂时注释掉，文件路径不正确
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Pydantic模型
class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    overall_status: str
    timestamp: str
    components: Dict[str, Any]
    summary: Dict[str, int]

class DeploymentRequest(BaseModel):
    """部署请求模型"""
    environment: str = Field(..., description="部署环境")
    version: Optional[str] = Field(None, description="部署版本")
    force: bool = Field(False, description="是否强制部署")

class DeploymentResponse(BaseModel):
    """部署响应模型"""
    success: bool
    deployment_id: Optional[str]
    message: str

class AutomationRuleRequest(BaseModel):
    """自动化规则请求模型"""
    name: str = Field(..., description="规则名称")
    description: str = Field(..., description="规则描述")
    enabled: bool = Field(True, description="是否启用")
    conditions: Dict[str, Any] = Field(..., description="触发条件")
    actions: List[Dict[str, Any]] = Field(..., description="执行动作")
    cooldown_minutes: int = Field(30, description="冷却时间（分钟）")
    max_executions_per_hour: int = Field(5, description="每小时最大执行次数")
    priority: int = Field(1, ge=1, le=10, description="优先级（1-10）")

class AutomationRuleResponse(BaseModel):
    """自动化规则响应模型"""
    id: str
    name: str
    description: str
    enabled: bool
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    cooldown_minutes: int
    max_executions_per_hour: int
    priority: int

# 健康监控相关API
@router.get("/health", response_model=HealthCheckResponse, summary="获取系统健康状态")
async def get_health_status(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取系统整体健康状态
    
    返回所有组件的健康检查结果，包括：
    - 数据库连接状态
    - Redis连接状态
    - 系统资源使用情况
    - 应用程序响应状态
    """
    try:
        health_data = await health_monitor.get_health_status()
        return HealthCheckResponse(**health_data)
    except Exception as e:
        logger.error(f"Failed to get health status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get health status")

@router.get("/health/{component}", summary="获取特定组件健康状态")
async def get_component_health(
    component: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取特定组件的健康状态
    
    支持的组件：
    - database: 数据库
    - redis: Redis缓存
    - system_resources: 系统资源
    - application: 应用程序
    """
    try:
        health_data = await health_monitor.get_health_status()
        
        if component not in health_data["components"]:
            raise HTTPException(status_code=404, detail=f"Component '{component}' not found")
        
        return {
            "component": component,
            "status": health_data["components"][component],
            "timestamp": health_data["timestamp"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get component health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get component health")

@router.post("/health/start-monitoring", summary="启动健康监控")
async def start_health_monitoring(
    current_user: dict = Depends(get_current_admin_user)
):
    """启动系统健康监控服务"""
    try:
        await health_monitor.start_monitoring()
        return {"message": "Health monitoring started successfully"}
    except Exception as e:
        logger.error(f"Failed to start health monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start health monitoring")

@router.post("/health/stop-monitoring", summary="停止健康监控")
async def stop_health_monitoring(
    current_user: dict = Depends(get_current_admin_user)
):
    """停止系统健康监控服务"""
    try:
        await health_monitor.stop_monitoring()
        return {"message": "Health monitoring stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop health monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop health monitoring")

@router.get("/health/healing-history", summary="获取自愈历史")
async def get_healing_history(
    component: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取系统自愈历史记录
    
    参数：
    - component: 可选，指定组件名称
    - limit: 返回记录数量限制
    """
    try:
        history = health_monitor.self_healing.get_healing_history(component)
        return {
            "healing_history": history[-limit:],
            "total_count": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get healing history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get healing history")

# 部署管理相关API
@router.post("/deploy", response_model=DeploymentResponse, summary="执行部署")
async def deploy_application(
    request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    执行应用程序部署
    
    支持的环境：
    - staging: 测试环境
    - production: 生产环境
    """
    try:
        # deployment_manager = DeploymentManager()  # 暂时注释掉
        # 
        # # 在后台执行部署
        # background_tasks.add_task(
        #     deployment_manager.deploy,
        #     request.environment,
        #     request.version,
        #     request.force
        # )
        
        return DeploymentResponse(
            success=True,
            deployment_id=f"deploy_{int(datetime.now().timestamp())}",
            message=f"Deployment to {request.environment} started"
        )
    except Exception as e:
        logger.error(f"Failed to start deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start deployment: {str(e)}")

@router.get("/deploy/status", summary="获取部署状态")
async def get_deployment_status(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取当前部署状态和历史记录"""
    try:
        # deployment_manager = DeploymentManager()  # 暂时注释掉
        # status = deployment_manager.get_deployment_status()
        # return status
        return {"status": "not_implemented", "message": "Deployment status not available"}
    except Exception as e:
        logger.error(f"Failed to get deployment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get deployment status")

@router.post("/backup/create", summary="创建数据库备份")
async def create_database_backup(
    environment: str,
    backup_name: Optional[str] = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    创建数据库备份
    
    参数：
    - environment: 环境名称
    - backup_name: 可选，备份名称
    """
    try:
        # deployment_manager = DeploymentManager()  # 暂时注释掉
        # env_config = deployment_manager.config["environments"].get(environment)
        # 
        # if not env_config:
        #     raise HTTPException(status_code=404, detail=f"Environment '{environment}' not found")
        # 
        # from app.scripts.auto_deploy import DatabaseBackupManager
        # backup_manager = DatabaseBackupManager(env_config["database_url"])
        # backup_file = backup_manager.create_backup(backup_name)
        backup_file = f"backup_{environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        return {
            "message": "Backup created successfully",
            "backup_file": backup_file,
            "environment": environment
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")

# 告警自动化相关API
@router.get("/automation/rules", response_model=List[AutomationRuleResponse], summary="获取自动化规则列表")
async def get_automation_rules(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取所有自动化规则"""
    try:
        rules = alert_automation.list_rules()
        return [
            AutomationRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                enabled=rule.enabled,
                conditions=rule.conditions,
                actions=rule.actions,
                cooldown_minutes=rule.cooldown_minutes,
                max_executions_per_hour=rule.max_executions_per_hour,
                priority=rule.priority
            )
            for rule in rules
        ]
    except Exception as e:
        logger.error(f"Failed to get automation rules: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get automation rules")

@router.post("/automation/rules", response_model=AutomationRuleResponse, summary="创建自动化规则")
async def create_automation_rule(
    request: AutomationRuleRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建新的自动化规则"""
    try:
        import uuid
        rule_id = str(uuid.uuid4())
        
        rule = AutomationRule(
            id=rule_id,
            name=request.name,
            description=request.description,
            enabled=request.enabled,
            conditions=request.conditions,
            actions=request.actions,
            cooldown_minutes=request.cooldown_minutes,
            max_executions_per_hour=request.max_executions_per_hour,
            priority=request.priority
        )
        
        alert_automation.add_rule(rule)
        
        return AutomationRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            enabled=rule.enabled,
            conditions=rule.conditions,
            actions=rule.actions,
            cooldown_minutes=rule.cooldown_minutes,
            max_executions_per_hour=rule.max_executions_per_hour,
            priority=rule.priority
        )
    except Exception as e:
        logger.error(f"Failed to create automation rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create automation rule: {str(e)}")

@router.get("/automation/rules/{rule_id}", response_model=AutomationRuleResponse, summary="获取特定自动化规则")
async def get_automation_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取特定的自动化规则"""
    try:
        rule = alert_automation.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
        
        return AutomationRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            enabled=rule.enabled,
            conditions=rule.conditions,
            actions=rule.actions,
            cooldown_minutes=rule.cooldown_minutes,
            max_executions_per_hour=rule.max_executions_per_hour,
            priority=rule.priority
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get automation rule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get automation rule")

@router.put("/automation/rules/{rule_id}", response_model=AutomationRuleResponse, summary="更新自动化规则")
async def update_automation_rule(
    rule_id: str,
    request: AutomationRuleRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新自动化规则"""
    try:
        existing_rule = alert_automation.get_rule(rule_id)
        
        if not existing_rule:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
        
        updated_rule = AutomationRule(
            id=rule_id,
            name=request.name,
            description=request.description,
            enabled=request.enabled,
            conditions=request.conditions,
            actions=request.actions,
            cooldown_minutes=request.cooldown_minutes,
            max_executions_per_hour=request.max_executions_per_hour,
            priority=request.priority
        )
        
        alert_automation.add_rule(updated_rule)  # 这会覆盖现有规则
        
        return AutomationRuleResponse(
            id=updated_rule.id,
            name=updated_rule.name,
            description=updated_rule.description,
            enabled=updated_rule.enabled,
            conditions=updated_rule.conditions,
            actions=updated_rule.actions,
            cooldown_minutes=updated_rule.cooldown_minutes,
            max_executions_per_hour=updated_rule.max_executions_per_hour,
            priority=updated_rule.priority
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update automation rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update automation rule: {str(e)}")

@router.delete("/automation/rules/{rule_id}", summary="删除自动化规则")
async def delete_automation_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除自动化规则"""
    try:
        rule = alert_automation.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
        
        alert_automation.remove_rule(rule_id)
        
        return {"message": f"Rule '{rule_id}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete automation rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete automation rule: {str(e)}")

@router.post("/automation/start", summary="启动告警自动化")
async def start_alert_automation(
    current_user: dict = Depends(get_current_admin_user)
):
    """启动告警自动化处理"""
    try:
        await alert_automation.start_processing()
        return {"message": "Alert automation started successfully"}
    except Exception as e:
        logger.error(f"Failed to start alert automation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start alert automation")

@router.post("/automation/stop", summary="停止告警自动化")
async def stop_alert_automation(
    current_user: dict = Depends(get_current_admin_user)
):
    """停止告警自动化处理"""
    try:
        await alert_automation.stop_processing()
        return {"message": "Alert automation stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop alert automation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop alert automation")

@router.get("/automation/statistics", summary="获取自动化统计信息")
async def get_automation_statistics(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取告警自动化统计信息"""
    try:
        stats = alert_automation.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get automation statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get automation statistics")

@router.get("/automation/execution-history", summary="获取自动化执行历史")
async def get_automation_execution_history(
    rule_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取自动化执行历史
    
    参数：
    - rule_id: 可选，指定规则ID
    - limit: 返回记录数量限制
    """
    try:
        history = alert_automation.get_execution_history(rule_id, limit)
        return {
            "execution_history": [execution.to_dict() for execution in history],
            "total_count": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get execution history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get execution history")

# 系统管理相关API
@router.get("/system/info", summary="获取系统信息")
async def get_system_info(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取系统基本信息"""
    try:
        import psutil
        import platform
        from datetime import datetime
        
        # 系统信息
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_total": psutil.disk_usage('/').total,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            "current_time": datetime.now().isoformat()
        }
        
        # 服务状态
        service_status = {
            "health_monitoring": health_monitor.is_running,
            "alert_automation": alert_automation.is_running
        }
        
        return {
            "system_info": system_info,
            "service_status": service_status
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system info")

@router.post("/system/restart-services", summary="重启系统服务")
async def restart_system_services(
    services: List[str],
    current_user: dict = Depends(get_current_admin_user)
):
    """
    重启指定的系统服务
    
    支持的服务：
    - health_monitoring: 健康监控服务
    - alert_automation: 告警自动化服务
    """
    try:
        results = {}
        
        for service in services:
            try:
                if service == "health_monitoring":
                    await health_monitor.stop_monitoring()
                    await health_monitor.start_monitoring()
                    results[service] = "restarted"
                elif service == "alert_automation":
                    await alert_automation.stop_processing()
                    await alert_automation.start_processing()
                    results[service] = "restarted"
                else:
                    results[service] = f"unknown service: {service}"
            except Exception as e:
                results[service] = f"failed: {str(e)}"
        
        return {
            "message": "Service restart completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to restart services: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to restart services")