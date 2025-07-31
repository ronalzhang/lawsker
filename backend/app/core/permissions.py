"""
增强权限控制系统
基于角色的访问控制(RBAC)和属性基础访问控制(ABAC)
"""
import json
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from functools import wraps
from fastapi import HTTPException, status, Request, Depends
from app.core.security import get_current_user
from app.core.logging import get_logger

logger = get_logger(__name__)

class PermissionAction(str, Enum):
    """权限操作枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    EXPORT = "export"
    IMPORT = "import"

class ResourceType(str, Enum):
    """资源类型枚举"""
    USER = "user"
    LAWYER = "lawyer"
    CASE = "case"
    DOCUMENT = "document"
    PAYMENT = "payment"
    REPORT = "report"
    SYSTEM = "system"
    ADMIN = "admin"

class Role(str, Enum):
    """角色枚举"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    LAWYER = "lawyer"
    USER = "user"
    GUEST = "guest"

class Permission:
    """权限类"""
    
    def __init__(
        self,
        resource: ResourceType,
        action: PermissionAction,
        conditions: Optional[Dict[str, Any]] = None,
        description: str = ""
    ):
        self.resource = resource
        self.action = action
        self.conditions = conditions or {}
        self.description = description
        self.key = f"{resource}:{action}"
    
    def __str__(self):
        return self.key
    
    def __repr__(self):
        return f"Permission({self.key})"
    
    def __eq__(self, other):
        if isinstance(other, Permission):
            return self.key == other.key
        return str(self) == str(other)
    
    def __hash__(self):
        return hash(self.key)

class PermissionRegistry:
    """权限注册表"""
    
    def __init__(self):
        self._permissions: Dict[str, Permission] = {}
        self._role_permissions: Dict[Role, List[Permission]] = {}
        self._initialize_default_permissions()
    
    def register_permission(self, permission: Permission):
        """注册权限"""
        self._permissions[permission.key] = permission
        logger.debug(f"Registered permission: {permission.key}")
    
    def get_permission(self, key: str) -> Optional[Permission]:
        """获取权限"""
        return self._permissions.get(key)
    
    def assign_permission_to_role(self, role: Role, permission: Permission):
        """为角色分配权限"""
        if role not in self._role_permissions:
            self._role_permissions[role] = []
        
        if permission not in self._role_permissions[role]:
            self._role_permissions[role].append(permission)
            logger.debug(f"Assigned permission {permission.key} to role {role}")
    
    def get_role_permissions(self, role: Role) -> List[Permission]:
        """获取角色权限"""
        return self._role_permissions.get(role, [])
    
    def _initialize_default_permissions(self):
        """初始化默认权限"""
        # 用户管理权限
        user_permissions = [
            Permission(ResourceType.USER, PermissionAction.CREATE, description="创建用户"),
            Permission(ResourceType.USER, PermissionAction.READ, description="查看用户"),
            Permission(ResourceType.USER, PermissionAction.UPDATE, description="更新用户"),
            Permission(ResourceType.USER, PermissionAction.DELETE, description="删除用户"),
        ]
        
        # 律师管理权限
        lawyer_permissions = [
            Permission(ResourceType.LAWYER, PermissionAction.CREATE, description="创建律师"),
            Permission(ResourceType.LAWYER, PermissionAction.READ, description="查看律师"),
            Permission(ResourceType.LAWYER, PermissionAction.UPDATE, description="更新律师"),
            Permission(ResourceType.LAWYER, PermissionAction.DELETE, description="删除律师"),
            Permission(ResourceType.LAWYER, PermissionAction.APPROVE, description="审核律师"),
        ]
        
        # 案件管理权限
        case_permissions = [
            Permission(ResourceType.CASE, PermissionAction.CREATE, description="创建案件"),
            Permission(ResourceType.CASE, PermissionAction.READ, description="查看案件"),
            Permission(ResourceType.CASE, PermissionAction.UPDATE, description="更新案件"),
            Permission(ResourceType.CASE, PermissionAction.DELETE, description="删除案件"),
        ]
        
        # 文档管理权限
        document_permissions = [
            Permission(ResourceType.DOCUMENT, PermissionAction.CREATE, description="创建文档"),
            Permission(ResourceType.DOCUMENT, PermissionAction.READ, description="查看文档"),
            Permission(ResourceType.DOCUMENT, PermissionAction.UPDATE, description="更新文档"),
            Permission(ResourceType.DOCUMENT, PermissionAction.DELETE, description="删除文档"),
        ]
        
        # 支付管理权限
        payment_permissions = [
            Permission(ResourceType.PAYMENT, PermissionAction.READ, description="查看支付"),
            Permission(ResourceType.PAYMENT, PermissionAction.UPDATE, description="更新支付"),
            Permission(ResourceType.PAYMENT, PermissionAction.APPROVE, description="审核支付"),
        ]
        
        # 报表权限
        report_permissions = [
            Permission(ResourceType.REPORT, PermissionAction.READ, description="查看报表"),
            Permission(ResourceType.REPORT, PermissionAction.EXPORT, description="导出报表"),
        ]
        
        # 系统管理权限
        system_permissions = [
            Permission(ResourceType.SYSTEM, PermissionAction.READ, description="查看系统信息"),
            Permission(ResourceType.SYSTEM, PermissionAction.UPDATE, description="更新系统配置"),
            Permission(ResourceType.SYSTEM, PermissionAction.EXECUTE, description="执行系统操作"),
        ]
        
        # 管理员权限
        admin_permissions = [
            Permission(ResourceType.ADMIN, PermissionAction.CREATE, description="创建管理员"),
            Permission(ResourceType.ADMIN, PermissionAction.READ, description="查看管理员"),
            Permission(ResourceType.ADMIN, PermissionAction.UPDATE, description="更新管理员"),
            Permission(ResourceType.ADMIN, PermissionAction.DELETE, description="删除管理员"),
        ]
        
        # 注册所有权限
        all_permissions = (
            user_permissions + lawyer_permissions + case_permissions +
            document_permissions + payment_permissions + report_permissions +
            system_permissions + admin_permissions
        )
        
        for permission in all_permissions:
            self.register_permission(permission)
        
        # 为角色分配权限
        self._assign_default_role_permissions(all_permissions)
    
    def _assign_default_role_permissions(self, all_permissions: List[Permission]):
        """为角色分配默认权限"""
        # 超级管理员 - 所有权限
        for permission in all_permissions:
            self.assign_permission_to_role(Role.SUPER_ADMIN, permission)
        
        # 管理员 - 除系统管理外的所有权限
        admin_permissions = [p for p in all_permissions if p.resource != ResourceType.SYSTEM]
        for permission in admin_permissions:
            self.assign_permission_to_role(Role.ADMIN, permission)
        
        # 经理 - 用户、律师、案件、报表权限
        manager_permissions = [
            p for p in all_permissions 
            if p.resource in [ResourceType.USER, ResourceType.LAWYER, ResourceType.CASE, ResourceType.REPORT]
        ]
        for permission in manager_permissions:
            self.assign_permission_to_role(Role.MANAGER, permission)
        
        # 律师 - 案件、文档权限（限制条件：只能操作自己的）
        lawyer_permissions = [
            p for p in all_permissions 
            if p.resource in [ResourceType.CASE, ResourceType.DOCUMENT] and p.action != PermissionAction.DELETE
        ]
        for permission in lawyer_permissions:
            # 添加条件：只能操作自己的资源
            permission.conditions = {"owner_only": True}
            self.assign_permission_to_role(Role.LAWYER, permission)
        
        # 普通用户 - 只读权限
        user_permissions = [
            p for p in all_permissions 
            if p.action == PermissionAction.READ and p.resource in [ResourceType.CASE, ResourceType.DOCUMENT]
        ]
        for permission in user_permissions:
            # 添加条件：只能查看自己的资源
            permission.conditions = {"owner_only": True}
            self.assign_permission_to_role(Role.USER, permission)

class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, registry: PermissionRegistry):
        self.registry = registry
    
    def check_permission(
        self,
        user: Dict[str, Any],
        resource: ResourceType,
        action: PermissionAction,
        resource_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """检查用户权限"""
        try:
            user_role = Role(user.get("role", "user"))
            user_permissions = self.registry.get_role_permissions(user_role)
            
            # 查找匹配的权限
            required_permission_key = f"{resource}:{action}"
            matching_permission = None
            
            for permission in user_permissions:
                if permission.key == required_permission_key:
                    matching_permission = permission
                    break
            
            if not matching_permission:
                logger.debug(f"Permission denied: {required_permission_key} not found for role {user_role}")
                return False
            
            # 检查条件
            if matching_permission.conditions:
                return self._check_conditions(
                    user, matching_permission.conditions, resource_data
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            return False
    
    def _check_conditions(
        self,
        user: Dict[str, Any],
        conditions: Dict[str, Any],
        resource_data: Optional[Dict[str, Any]]
    ) -> bool:
        """检查权限条件"""
        # 检查所有者条件
        if conditions.get("owner_only") and resource_data:
            resource_owner_id = resource_data.get("owner_id") or resource_data.get("user_id")
            if resource_owner_id != user.get("user_id"):
                logger.debug(f"Owner check failed: resource owner {resource_owner_id} != user {user.get('user_id')}")
                return False
        
        # 检查时间条件
        if "time_range" in conditions:
            # 实现时间范围检查
            pass
        
        # 检查IP条件
        if "allowed_ips" in conditions:
            # 实现IP检查
            pass
        
        # 检查其他自定义条件
        for condition_key, condition_value in conditions.items():
            if condition_key.startswith("custom_"):
                # 实现自定义条件检查
                pass
        
        return True
    
    def get_user_permissions(self, user: Dict[str, Any]) -> List[str]:
        """获取用户所有权限"""
        try:
            user_role = Role(user.get("role", "user"))
            permissions = self.registry.get_role_permissions(user_role)
            return [permission.key for permission in permissions]
        except Exception as e:
            logger.error(f"Get user permissions error: {str(e)}")
            return []

# 全局权限注册表和检查器
permission_registry = PermissionRegistry()
permission_checker = PermissionChecker(permission_registry)

def require_permission(
    resource: ResourceType,
    action: PermissionAction,
    get_resource_data: Optional[Callable] = None
):
    """权限验证装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            try:
                current_user = await get_current_user(request)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # 获取资源数据（如果需要）
            resource_data = None
            if get_resource_data:
                try:
                    resource_data = await get_resource_data(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Failed to get resource data: {str(e)}")
            
            # 检查权限
            has_permission = permission_checker.check_permission(
                current_user, resource, action, resource_data
            )
            
            if not has_permission:
                logger.warning(
                    f"Permission denied - User: {current_user.get('user_id')} - "
                    f"Resource: {resource} - Action: {action}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for {resource}:{action}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_role(required_role: Role):
    """角色验证装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            try:
                current_user = await get_current_user(request)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = current_user.get("role")
            if user_role != required_role.value:
                logger.warning(
                    f"Role check failed - User: {current_user.get('user_id')} - "
                    f"Required: {required_role} - Actual: {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role.value}' required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_any_role(required_roles: List[Role]):
    """多角色验证装饰器（满足其中一个即可）"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            try:
                current_user = await get_current_user(request)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = current_user.get("role")
            required_role_values = [role.value for role in required_roles]
            
            if user_role not in required_role_values:
                logger.warning(
                    f"Role check failed - User: {current_user.get('user_id')} - "
                    f"Required: {required_role_values} - Actual: {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of roles {required_role_values} required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# 权限检查依赖注入
async def check_permission_dependency(
    resource: ResourceType,
    action: PermissionAction,
    current_user: dict = Depends(get_current_user)
) -> bool:
    """权限检查依赖"""
    return permission_checker.check_permission(current_user, resource, action)

# 获取用户权限依赖
async def get_user_permissions_dependency(
    current_user: dict = Depends(get_current_user)
) -> List[str]:
    """获取用户权限依赖"""
    return permission_checker.get_user_permissions(current_user)