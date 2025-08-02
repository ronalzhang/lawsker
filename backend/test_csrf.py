#!/usr/bin/env python3
"""
测试CSRF路由
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from app.api.v1.api import api_router

app = FastAPI()
app.include_router(api_router, prefix="/api/v1")

# 打印所有路由
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"Path: {route.path}, Methods: {getattr(route, 'methods', 'N/A')}")

print("\n" + "="*50)
print("检查CSRF路由是否存在...")

# 检查CSRF路由
csrf_routes = [route for route in app.routes if 'csrf' in str(route.path).lower()]
for route in csrf_routes:
    print(f"CSRF Route: {route.path}") 