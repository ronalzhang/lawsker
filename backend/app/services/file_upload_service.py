"""
安全文件上传服务 - 简化版本
处理银行机构坏账数据上传
"""

import os
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.statistics import DataUploadRecord
from app.models.user import User


class FileUploadService:
    """安全文件上传服务"""
    
    # 允许的文件类型和大小限制
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv', '.pdf', '.doc', '.docx'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_FILES_PER_UPLOAD = 10
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = Path('/tmp/lawsker_uploads')
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_files(
        self,
        files: List[UploadFile],
        user_id: uuid.UUID,
        data_type: str,
        description: str
    ) -> List[Dict[str, Any]]:
        """上传多个文件并进行安全验证"""
        if not files:
            raise HTTPException(status_code=400, detail="没有选择文件")
        
        if len(files) > self.MAX_FILES_PER_UPLOAD:
            raise HTTPException(
                status_code=400, 
                detail=f"一次最多上传{self.MAX_FILES_PER_UPLOAD}个文件"
            )
        
        results = []
        for file in files:
            try:
                result = await self._process_single_file(file, user_id, data_type, description)
                results.append(result)
            except Exception as e:
                results.append({
                    "filename": file.filename or "unknown",
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _process_single_file(
        self,
        file: UploadFile,
        user_id: uuid.UUID,
        data_type: str,
        description: str
    ) -> Dict[str, Any]:
        """处理单个文件上传"""
        
        # 检查文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 基础验证
        await self._validate_file_basic(file)
        
        # 读取文件内容
        file_content = await file.read()
        await file.seek(0)
        
        # 安全验证
        await self._validate_file_security(file.filename, file_content)
        
        # 保存文件
        file_path, file_hash = await self._save_file_securely(file, file_content)
        
        # 创建上传记录
        upload_record = await self._create_upload_record(
            user_id=user_id,
            file_name=file.filename,
            file_path=str(file_path),
            file_size=len(file_content),
            file_type=file.content_type or "application/octet-stream",
            file_hash=file_hash,
            data_type=data_type,
            description=description
        )
        
        return {
            "filename": file.filename,
            "success": True,
            "upload_id": str(upload_record.id),
            "file_size": len(file_content),
            "message": "文件上传成功"
        }
    
    async def _validate_file_basic(self, file: UploadFile):
        """基础文件验证"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 检查文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型：{file_ext}。支持的类型：{', '.join(self.ALLOWED_EXTENSIONS)}"
            )
    
    async def _validate_file_security(self, filename: str, content: bytes):
        """安全验证"""
        # 文件大小验证
        if len(content) > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超出限制：{len(content) / 1024 / 1024:.1f}MB"
            )
        
        # 简单的恶意内容检查
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
        ]
        
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                raise HTTPException(
                    status_code=400,
                    detail="文件包含可疑内容，上传被拒绝"
                )
    
    async def _save_file_securely(self, file: UploadFile, content: bytes):
        """安全保存文件"""
        # 生成安全的文件名
        file_hash = hashlib.sha256(content).hexdigest()
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        safe_filename = f"{uuid.uuid4()}_{file_hash[:8]}{file_ext}"
        
        # 创建日期目录
        date_dir = self.upload_dir / datetime.now().strftime("%Y/%m/%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = date_dir / safe_filename
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 设置安全的文件权限
        os.chmod(file_path, 0o644)
        
        return file_path, file_hash
    
    async def _create_upload_record(
        self,
        user_id: uuid.UUID,
        file_name: str,
        file_path: str,
        file_size: int,
        file_type: str,
        file_hash: str,
        data_type: str,
        description: str
    ) -> DataUploadRecord:
        """创建上传记录"""
        
        record = DataUploadRecord(
            user_id=user_id,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            file_path=file_path,
            data_type=data_type,
            total_records=1,
            processed_records=1,
            failed_records=0,
            status="completed",
            error_details={},
            processing_notes=description
        )
        
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        
        return record
    
    async def get_upload_history(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[DataUploadRecord]:
        """获取用户上传历史"""
        
        query = select(DataUploadRecord).where(
            DataUploadRecord.user_id == user_id
        ).order_by(
            DataUploadRecord.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all()) 