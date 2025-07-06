#!/usr/bin/env python3
import http.server
import socketserver
import os
import urllib.parse

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # URL路由映射
        routes = {
            '/user': '/user-workspace.html',
            '/legal': '/lawyer-workspace.html',
            '/institution': '/institution-workspace.html',
            '/calculator': '/earnings-calculator.html',
            '/earnings-calculator': '/earnings-calculator.html',
            '/withdraw': '/withdrawal.html',
            '/submit': '/anonymous-task.html',
            '/auth': '/login.html',
            '/admin': '/admin-config.html',
            '/admin-pro': '/admin-config-optimized.html',
            '/console': '/dashboard.html'
        }
        
        # 处理重定向
        if self.path == '/sales':
            self.send_response(301)
            self.send_header('Location', '/user')
            self.end_headers()
            return
        
        # 检查是否是需要重写的路由
        if self.path in routes:
            self.path = routes[self.path]
        
        # 如果是根路径，重定向到index.html
        if self.path == '/':
            self.path = '/index.html'
        
        # 调用父类方法处理请求
        super().do_GET()

def main():
    PORT = 6060
    
    # 切换到正确的目录
    os.chdir('/root/lawsker/frontend')
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Lawsker frontend server running on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    main() 