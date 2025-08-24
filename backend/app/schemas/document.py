"""
文档相关的 Pydantic 模型
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """文档基础模型"""
    title: str = Field(..., description="文档标题")
    content: Optional[str] = Field(None, description="文档内容")
    category: Optional[str] = Field(None, description="文档分类")
    tags: Optional[List[str]] = Field(default_factory=list, description="文档标签")
    is_public: bool = Field(default=False, description="是否公开")
    description: Optional[str] = Field(None, description="文档描述")


class DocumentCreate(DocumentBase):
    """创建文档模型"""
    pass


class DocumentUpdate(BaseModel):
    """更新文档模型"""
    title: Optional[str] = Field(None, description="文档标题")
    content: Optional[str] = Field(None, description="文档内容")
    category: Optional[str] = Field(None, description="文档分类")
    tags: Optional[List[str]] = Field(None, description="文档标签")
    is_public: Optional[bool] = Field(None, description="是否公开")
    description: Optional[str] = Field(None, description="文档描述")


class Document(DocumentBase):
    """文档响应模型"""
    id: int = Field(..., description="文档ID")
    user_id: int = Field(..., description="创建用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小")
    file_type: Optional[str] = Field(None, description="文件类型")
    download_count: int = Field(default=0, description="下载次数")
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """文档列表响应模型"""
    documents: List[Document]
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    
    
class DocumentUploadResponse(BaseModel):
    """文档上传响应模型"""
    message: str = Field(..., description="响应消息")
    document_id: Optional[int] = Field(None, description="文档ID")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小")