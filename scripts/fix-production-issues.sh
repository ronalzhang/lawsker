#!/bin/bash

# Lawsker 生产环境问题修复脚本
# 针对验证中发现的问题进行修复

# 🎨 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Lawsker 生产环境问题修复                         ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}基于最新验证结果，发现以下问题需要修复：${NC}"
echo -e "${RED}1. API 文档访问异常 (/docs, /redoc 返回 500)${NC}"
echo -e "${RED}2. 部分 API 端点不存在 (/api/v1/documents, /api/v1/users)${NC}"
echo -e "${RED}3. 404 页面处理异常${NC}"

echo -e "\n${PURPLE}🔍 问题分析和修复建议${NC}"
echo "=================================================="

# 🔍 1. 检查 API 路由配置
echo -e "\n${BLUE}📋 1. 检查 API 路由配置${NC}"
echo -e "${YELLOW}问题: /api/v1/documents 和 /api/v1/users 返回 404${NC}"
echo -e "${GREEN}建议修复步骤:${NC}"

# 检查相关文件是否存在
if [ -f "backend/app/api/v1/endpoints/documents.py" ]; then
    echo -e "${GREEN}✅ documents.py 文件存在${NC}"
else
    echo -e "${RED}❌ documents.py 文件不存在，需要创建${NC}"
fi

if [ -f "backend/app/api/v1/endpoints/users.py" ]; then
    echo -e "${GREEN}✅ users.py 文件存在${NC}"
else
    echo -e "${RED}❌ users.py 文件不存在，需要创建${NC}"
fi

# 检查路由注册
echo -e "\n${YELLOW}检查路由注册文件:${NC}"
if [ -f "backend/app/api/v1/api.py" ]; then
    echo -e "${GREEN}✅ api.py 路由文件存在${NC}"
    if grep -q "documents" backend/app/api/v1/api.py; then
        echo -e "${GREEN}✅ documents 路由已注册${NC}"
    else
        echo -e "${RED}❌ documents 路由未注册${NC}"
    fi
    if grep -q "users" backend/app/api/v1/api.py; then
        echo -e "${GREEN}✅ users 路由已注册${NC}"
    else
        echo -e "${RED}❌ users 路由未注册${NC}"
    fi
else
    echo -e "${RED}❌ api.py 路由文件不存在${NC}"
fi

# 🔍 2. 检查 FastAPI 文档配置
echo -e "\n${BLUE}📚 2. 检查 FastAPI 文档配置${NC}"
echo -e "${YELLOW}问题: /docs 和 /redoc 返回 500 错误${NC}"
echo -e "${GREEN}可能原因:${NC}"
echo -e "${YELLOW}  - OpenAPI schema 生成错误${NC}"
echo -e "${YELLOW}  - 某个 API 端点的 Pydantic 模型有问题${NC}"
echo -e "${YELLOW}  - 依赖注入配置错误${NC}"

# 检查主应用文件
if [ -f "backend/app/main.py" ]; then
    echo -e "${GREEN}✅ main.py 文件存在${NC}"
    if grep -q "docs_url" backend/app/main.py; then
        echo -e "${GREEN}✅ 文档 URL 配置存在${NC}"
    else
        echo -e "${YELLOW}⚠️  文档 URL 配置可能使用默认值${NC}"
    fi
else
    echo -e "${RED}❌ main.py 文件不存在${NC}"
fi

# 🔍 3. 生成修复脚本
echo -e "\n${BLUE}🛠️ 3. 生成修复脚本${NC}"

# 创建缺失的 API 端点文件
if [ ! -f "backend/app/api/v1/endpoints/documents.py" ]; then
    echo -e "${YELLOW}创建 documents.py 端点文件...${NC}"
    cat > backend/app/api/v1/endpoints/documents.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.document import Document, DocumentCreate, DocumentUpdate

router = APIRouter()

@router.get("/", response_model=List[Document])
def get_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取文档列表
    """
    # TODO: 实现文档列表获取逻辑
    return []

@router.post("/", response_model=Document)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新文档
    """
    # TODO: 实现文档创建逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="文档创建功能正在开发中"
    )

@router.get("/{document_id}", response_model=Document)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定文档
    """
    # TODO: 实现文档获取逻辑
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="文档不存在"
    )

@router.put("/{document_id}", response_model=Document)
def update_document(
    document_id: int,
    document: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新文档
    """
    # TODO: 实现文档更新逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="文档更新功能正在开发中"
    )

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除文档
    """
    # TODO: 实现文档删除逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="文档删除功能正在开发中"
    )

@router.post("/upload")
def upload_document(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文档
    """
    # TODO: 实现文档上传逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="文档上传功能正在开发中"
    )
EOF
    echo -e "${GREEN}✅ documents.py 文件已创建${NC}"
fi

if [ ! -f "backend/app/api/v1/endpoints/users.py" ]; then
    echo -e "${YELLOW}创建 users.py 端点文件...${NC}"
    cat > backend/app/api/v1/endpoints/users.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_current_user, get_db, get_current_active_superuser
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate

router = APIRouter()

@router.get("/", response_model=List[UserSchema])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    获取用户列表 (仅管理员)
    """
    # TODO: 实现用户列表获取逻辑
    return []

@router.post("/", response_model=UserSchema)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    创建新用户 (仅管理员)
    """
    # TODO: 实现用户创建逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="用户创建功能正在开发中"
    )

@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户信息
    """
    # TODO: 实现用户信息更新逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="用户信息更新功能正在开发中"
    )

@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    获取指定用户信息 (仅管理员)
    """
    # TODO: 实现用户信息获取逻辑
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="用户不存在"
    )

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    更新用户信息 (仅管理员)
    """
    # TODO: 实现用户信息更新逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="用户信息更新功能正在开发中"
    )

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    删除用户 (仅管理员)
    """
    # TODO: 实现用户删除逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="用户删除功能正在开发中"
    )

@router.get("/profile")
def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    获取用户资料
    """
    # TODO: 实现用户资料获取逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="用户资料功能正在开发中"
    )
EOF
    echo -e "${GREEN}✅ users.py 文件已创建${NC}"
fi

# 检查并更新路由注册
echo -e "\n${YELLOW}检查路由注册...${NC}"
if [ -f "backend/app/api/v1/api.py" ]; then
    # 检查是否需要添加路由
    need_update=false
    
    if ! grep -q "from app.api.v1.endpoints import documents" backend/app/api/v1/api.py; then
        echo -e "${YELLOW}需要添加 documents 路由导入${NC}"
        need_update=true
    fi
    
    if ! grep -q "from app.api.v1.endpoints import users" backend/app/api/v1/api.py; then
        echo -e "${YELLOW}需要添加 users 路由导入${NC}"
        need_update=true
    fi
    
    if ! grep -q 'api_router.include_router(documents.router, prefix="/documents"' backend/app/api/v1/api.py; then
        echo -e "${YELLOW}需要注册 documents 路由${NC}"
        need_update=true
    fi
    
    if ! grep -q 'api_router.include_router(users.router, prefix="/users"' backend/app/api/v1/api.py; then
        echo -e "${YELLOW}需要注册 users 路由${NC}"
        need_update=true
    fi
    
    if [ "$need_update" = true ]; then
        echo -e "${YELLOW}正在更新路由注册...${NC}"
        # 备份原文件
        cp backend/app/api/v1/api.py backend/app/api/v1/api.py.backup
        
        # 添加导入和路由注册的示例
        echo -e "${GREEN}请手动更新 backend/app/api/v1/api.py 文件，添加以下内容:${NC}"
        echo -e "${CYAN}"
        cat << 'EOF'
# 在导入部分添加:
from app.api.v1.endpoints import documents, users

# 在路由注册部分添加:
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
EOF
        echo -e "${NC}"
    else
        echo -e "${GREEN}✅ 路由注册已完整${NC}"
    fi
fi

# 🔍 4. 创建文档修复脚本
echo -e "\n${BLUE}📚 4. FastAPI 文档问题修复${NC}"
echo -e "${GREEN}建议检查步骤:${NC}"
echo -e "${YELLOW}1. 检查所有 Pydantic 模型是否正确定义${NC}"
echo -e "${YELLOW}2. 检查是否有循环导入问题${NC}"
echo -e "${YELLOW}3. 检查依赖注入是否正确配置${NC}"
echo -e "${YELLOW}4. 临时禁用有问题的端点，逐个排查${NC}"

# 创建文档测试脚本
cat > scripts/test-docs-generation.py << 'EOF'
#!/usr/bin/env python3
"""
FastAPI 文档生成测试脚本
用于排查文档生成问题
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from app.main import app
    print("✅ 应用导入成功")
    
    # 尝试生成 OpenAPI schema
    try:
        schema = app.openapi()
        print("✅ OpenAPI schema 生成成功")
        print(f"📊 发现 {len(schema.get('paths', {}))} 个 API 路径")
    except Exception as e:
        print(f"❌ OpenAPI schema 生成失败: {e}")
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f"❌ 应用导入失败: {e}")
    import traceback
    traceback.print_exc()
EOF

chmod +x scripts/test-docs-generation.py
echo -e "${GREEN}✅ 文档测试脚本已创建: scripts/test-docs-generation.py${NC}"

# 🔍 5. 部署建议
echo -e "\n${BLUE}🚀 5. 部署建议${NC}"
echo -e "${GREEN}修复完成后的部署步骤:${NC}"
echo -e "${YELLOW}1. 提交代码更改${NC}"
echo -e "${YELLOW}2. 推送到 GitHub${NC}"
echo -e "${YELLOW}3. 在服务器上拉取更新${NC}"
echo -e "${YELLOW}4. 重启 PM2 服务${NC}"
echo -e "${YELLOW}5. 运行验证脚本确认修复${NC}"

echo -e "\n${CYAN}修复脚本执行完成！${NC}"
echo -e "${YELLOW}请按照上述建议手动完成剩余的修复步骤。${NC}"
echo -e "${GREEN}修复完成后，运行以下命令验证:${NC}"
echo -e "${BLUE}./scripts/test-production-remote.sh${NC}"

exit 0