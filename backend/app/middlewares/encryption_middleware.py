"""
数据传输加密中间件
实现端到端加密和数据脱敏
"""
import json
import gzip
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.encryption import encryption_manager, mask_sensitive_data
from app.core.logging import get_logger

logger = get_logger(__name__)

class EncryptionMiddleware(BaseHTTPMiddleware):
    """数据传输加密中间件"""
    
    def __init__(self, app: ASGIApp, enable_compression: bool = True):
        super().__init__(app)
        self.enable_compression = enable_compression
        self.sensitive_endpoints = {
            "/api/v1/users/profile",
            "/api/v1/lawyers/qualification",
            "/api/v1/auth/register",
            "/api/v1/users/update-profile"
        }
        self.masking_fields = {
            "phone_number": "phone",
            "email": "email", 
            "id_card_number": "id_card",
            "bank_card": "bank_card",
            "full_name": "name",
            "address": "address"
        }
    
    async def dispatch(self, request: Request, call_next):
        """处理请求和响应"""
        try:
            # 处理请求
            if await self._should_decrypt_request(request):
                request = await self._decrypt_request(request)
            
            # 执行请求
            response = await call_next(request)
            
            # 处理响应
            if await self._should_encrypt_response(request, response):
                response = await self._encrypt_response(request, response)
            elif await self._should_mask_response(request, response):
                response = await self._mask_response(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Encryption middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    async def _should_decrypt_request(self, request: Request) -> bool:
        """判断是否需要解密请求"""
        # 检查请求头中是否包含加密标识
        return (
            request.headers.get("X-Encrypted-Request") == "true" and
            request.method in ["POST", "PUT", "PATCH"]
        )
    
    async def _decrypt_request(self, request: Request) -> Request:
        """解密请求数据"""
        try:
            body = await request.body()
            if not body:
                return request
            
            # 解密请求体
            encrypted_data = json.loads(body.decode())
            if "encrypted_payload" in encrypted_data:
                decrypted_data = encryption_manager.decrypt_json(
                    encrypted_data["encrypted_payload"]
                )
                
                # 重新构建请求
                new_body = json.dumps(decrypted_data).encode()
                request._body = new_body
                
                logger.info(f"Decrypted request for {request.url.path}")
            
            return request
            
        except Exception as e:
            logger.error(f"Request decryption failed: {str(e)}")
            return request
    
    async def _should_encrypt_response(self, request: Request, response: Response) -> bool:
        """判断是否需要加密响应"""
        return (
            request.headers.get("X-Encrypt-Response") == "true" and
            response.status_code == 200 and
            hasattr(response, 'body')
        )
    
    async def _encrypt_response(self, request: Request, response: Response) -> Response:
        """加密响应数据"""
        try:
            if hasattr(response, 'body'):
                body = response.body
                if body:
                    # 解析响应数据
                    response_data = json.loads(body.decode())
                    
                    # 加密响应数据
                    encrypted_payload = encryption_manager.encrypt_json(response_data)
                    
                    # 构建加密响应
                    encrypted_response = {
                        "encrypted": True,
                        "payload": encrypted_payload,
                        "timestamp": int(datetime.now().timestamp())
                    }
                    
                    # 压缩响应（可选）
                    response_body = json.dumps(encrypted_response).encode()
                    if self.enable_compression and len(response_body) > 1024:
                        response_body = gzip.compress(response_body)
                        headers = dict(response.headers)
                        headers["Content-Encoding"] = "gzip"
                        headers["X-Encrypted-Response"] = "true"
                    else:
                        headers = dict(response.headers)
                        headers["X-Encrypted-Response"] = "true"
                    
                    return Response(
                        content=response_body,
                        status_code=response.status_code,
                        headers=headers,
                        media_type="application/json"
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Response encryption failed: {str(e)}")
            return response
    
    async def _should_mask_response(self, request: Request, response: Response) -> bool:
        """判断是否需要脱敏响应"""
        return (
            request.url.path in self.sensitive_endpoints and
            response.status_code == 200 and
            request.headers.get("X-Mask-Sensitive") == "true"
        )
    
    async def _mask_response(self, request: Request, response: Response) -> Response:
        """脱敏响应数据"""
        try:
            if hasattr(response, 'body'):
                body = response.body
                if body:
                    # 解析响应数据
                    response_data = json.loads(body.decode())
                    
                    # 递归脱敏敏感字段
                    masked_data = self._mask_sensitive_fields(response_data)
                    
                    # 构建脱敏响应
                    response_body = json.dumps(masked_data).encode()
                    
                    return Response(
                        content=response_body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type="application/json"
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Response masking failed: {str(e)}")
            return response
    
    def _mask_sensitive_fields(self, data: Any) -> Any:
        """递归脱敏敏感字段"""
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if key in self.masking_fields:
                    # 脱敏敏感字段
                    if value and isinstance(value, str):
                        masked_data[key] = mask_sensitive_data(value, self.masking_fields[key])
                    else:
                        masked_data[key] = value
                elif isinstance(value, (dict, list)):
                    # 递归处理嵌套数据
                    masked_data[key] = self._mask_sensitive_fields(value)
                else:
                    masked_data[key] = value
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_fields(item) for item in data]
        else:
            return data


class TransmissionEncryption:
    """传输加密工具类"""
    
    @staticmethod
    def encrypt_request_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """加密请求载荷"""
        try:
            encrypted_payload = encryption_manager.encrypt_json(data)
            return {
                "encrypted_payload": encrypted_payload,
                "timestamp": int(datetime.now().timestamp())
            }
        except Exception as e:
            logger.error(f"Request payload encryption failed: {str(e)}")
            return data
    
    @staticmethod
    def decrypt_response_payload(encrypted_response: Dict[str, Any]) -> Dict[str, Any]:
        """解密响应载荷"""
        try:
            if encrypted_response.get("encrypted") and "payload" in encrypted_response:
                return encryption_manager.decrypt_json(encrypted_response["payload"])
            return encrypted_response
        except Exception as e:
            logger.error(f"Response payload decryption failed: {str(e)}")
            return encrypted_response
    
    @staticmethod
    def create_secure_headers() -> Dict[str, str]:
        """创建安全请求头"""
        return {
            "X-Encrypted-Request": "true",
            "X-Encrypt-Response": "true",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def create_masking_headers() -> Dict[str, str]:
        """创建脱敏请求头"""
        return {
            "X-Mask-Sensitive": "true",
            "Content-Type": "application/json"
        }


# 导出中间件和工具
__all__ = ["EncryptionMiddleware", "TransmissionEncryption"]