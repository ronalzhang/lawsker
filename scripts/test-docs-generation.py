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
