#!/usr/bin/env python3
"""
批量更新HTML文件中的链接为安全路径
"""

import os
import re
import glob

# 定义路径映射
PATH_MAPPING = {
    'index.html': '/',
    'dashboard.html': '/console',
    'sales-workspace.html': '/sales',
    'lawyer-workspace.html': '/legal',
    'institution-workspace.html': '/institution',
    'earnings-calculator.html': '/calculator',
    'withdrawal.html': '/withdraw',
    'anonymous-task.html': '/submit',
    'login.html': '/auth',
    'admin-config.html': '/admin',
    'admin-config-optimized.html': '/admin-pro'
}

def update_links_in_file(file_path):
    """更新单个文件中的链接"""
    print(f"正在处理文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 更新href链接
    for old_path, new_path in PATH_MAPPING.items():
        # 匹配 href="filename.html" 格式
        pattern = rf'href=["\']({re.escape(old_path)})["\']'
        content = re.sub(pattern, f'href="{new_path}"', content)
        
        # 匹配 onclick="navigateTo('filename.html')" 格式
        pattern = rf"navigateTo\(['\"]({re.escape(old_path)})['\"]\)"
        content = re.sub(pattern, f"navigateTo('{new_path}')", content)
        
        # 匹配 window.location.href = 'filename.html' 格式
        pattern = rf"window\.location\.href\s*=\s*['\"]({re.escape(old_path)})['\"]\s*;"
        content = re.sub(pattern, f"window.location.href = '{new_path}';", content)
    
    # 特殊处理：更新workspaceMap中的路径
    workspace_map_pattern = r"workspaceMap\[selectedRole\]\s*\|\|\s*['\"]dashboard\.html['\"]"
    content = re.sub(workspace_map_pattern, "workspaceMap[selectedRole] || '/console'", content)
    
    workspace_map_pattern2 = r"workspaceMap\[role\]\s*\|\|\s*['\"]dashboard\.html['\"]"
    content = re.sub(workspace_map_pattern2, "workspaceMap[role] || '/console'", content)
    
    # 如果内容有变化，写回文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已更新: {file_path}")
        return True
    else:
        print(f"⏭️  无需更新: {file_path}")
        return False

def main():
    """主函数"""
    print("🔄 开始批量更新HTML文件中的链接...")
    
    # 获取所有HTML文件
    html_files = glob.glob('frontend/*.html')
    
    updated_count = 0
    
    for file_path in html_files:
        if update_links_in_file(file_path):
            updated_count += 1
    
    print(f"\n✨ 更新完成！共更新了 {updated_count} 个文件")
    
    # 输出URL映射表
    print("\n📋 URL映射表:")
    print("=" * 50)
    for old_path, new_path in PATH_MAPPING.items():
        print(f"{old_path:<25} → {new_path}")
    
    print("\n🌐 访问方式:")
    print("=" * 50)
    print("首页: https://lawsker.com 或 https://156.227.235.192")
    print("控制台: https://lawsker.com/console")
    print("销售工作台: https://lawsker.com/sales")
    print("律师工作台: https://lawsker.com/legal")
    print("收益计算器: https://lawsker.com/calculator")
    print("提现管理: https://lawsker.com/withdraw")
    print("一键律师函: https://lawsker.com/submit")
    print("用户登录: https://lawsker.com/auth")
    print("系统管理: https://lawsker.com/admin")

if __name__ == "__main__":
    main() 