# Lawsker API接口文档

## 📋 目录

- [接口概述](#接口概述)
- [认证机制](#认证机制)
- [用户接口](#用户接口)
- [律师接口](#律师接口)
- [案件接口](#案件接口)
- [支付接口](#支付接口)
- [文件接口](#文件接口)
- [管理接口](#管理接口)
- [错误处理](#错误处理)

## 🎯 接口概述

### 基础信息
- **Base URL**: `https://api.lawsker.com`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8
- **请求方法**: GET, POST, PUT, DELETE

### 通用响应格式
```json
{
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": "2024-01-30T12:00:00Z"
}
```

### 状态码说明
- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 禁止访问
- `404`: 资源不存在
- `500`: 服务器内部错误

## 🔐 认证机制

### JWT Token认证
```http
Authorization: Bearer <token>
```

### 获取Token
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "password123"
}
```

响应:
```json
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "expires_in": 3600,
        "user": {
            "id": 1,
            "username": "user@example.com",
            "role": "user"
        }
    }
}
```

## 👤 用户接口

### 用户注册
```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123",
    "phone": "13800138000"
}
```

### 获取用户信息
```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

### 更新用户信息
```http
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
    "nickname": "新昵称",
    "avatar": "https://example.com/avatar.jpg"
}
```

## ⚖️ 律师接口

### 律师认证申请
```http
POST /api/v1/lawyers/apply
Authorization: Bearer <token>
Content-Type: application/json

{
    "real_name": "张律师",
    "license_number": "11010120180001234",
    "law_firm": "某某律师事务所",
    "specialties": ["民事诉讼", "合同纠纷"],
    "certificates": ["cert1.jpg", "cert2.jpg"]
}
```

### 获取律师列表
```http
GET /api/v1/lawyers?page=1&size=20&specialty=民事诉讼
```

### 获取律师详情
```http
GET /api/v1/lawyers/{lawyer_id}
```