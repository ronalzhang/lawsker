"""
CSRF Token API端点
"""
from fastapi import APIRouter, Response
from app.middlewares.csrf_middleware import get_csrf_token

router = APIRouter()

@router.get("/csrf-token")
async def get_csrf_token_endpoint(response: Response):
    """
    获取CSRF Token
    用于前端在发送POST/PUT/DELETE请求时包含CSRF保护
    """
    token_data = get_csrf_token()
    
    # 设置CSRF token到Cookie
    response.set_cookie(
        key="csrf_token",
        value=token_data["cookie_token"],
        max_age=3600,  # 1小时
        httponly=False,  # 需要被JavaScript访问
        secure=True,     # 生产环境必须为True
        samesite="strict"
    )
    
    return {
        "csrf_token": token_data["token"],
        "expires_in": 3600
    }