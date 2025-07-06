"""
文件上传API端点
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.file_upload_service import FileUploadService

router = APIRouter()


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    data_type: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传文件
    
    支持的文件类型：
    - Excel文件 (.xlsx, .xls)
    - CSV文件 (.csv)
    - PDF文件 (.pdf)
    - Word文档 (.doc, .docx)
    
    数据类型：
    - debt_collection: 坏账催收数据
    - legal_document: 法律文档
    - contract: 合同文件
    - other: 其他类型
    """
    
    service = FileUploadService(db)
    
    try:
        results = await service.upload_files(
            files=files,
            user_id=current_user.id,  # type: ignore
            data_type=data_type,
            description=description
        )
        
        return {
            "message": "文件上传处理完成",
            "results": results,
            "total_files": len(files),
            "successful_uploads": len([r for r in results if r.get("success")]),
            "failed_uploads": len([r for r in results if not r.get("success")])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/history")
async def get_upload_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户上传历史"""
    
    service = FileUploadService(db)
    
    try:
        history = await service.get_upload_history(
            user_id=current_user.id,  # type: ignore
            limit=limit,
            offset=offset
        )
        
        return {
            "message": "获取上传历史成功",
            "data": [
                {
                    "id": str(record.id),
                    "file_name": record.file_name,
                    "file_size": record.file_size,
                    "file_type": record.file_type,
                    "data_type": record.data_type,
                    "status": record.status,
                    "total_records": record.total_records,
                    "processed_records": record.processed_records,
                    "failed_records": record.failed_records,
                    "created_at": record.created_at.isoformat(),
                    "processing_notes": record.processing_notes
                }
                for record in history
            ],
            "total": len(history)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上传历史失败: {str(e)}")


@router.get("/types")
async def get_supported_types():
    """获取支持的文件类型和数据类型"""
    
    return {
        "file_types": {
            "excel": [".xlsx", ".xls"],
            "csv": [".csv"],
            "pdf": [".pdf"],
            "word": [".doc", ".docx"]
        },
        "data_types": {
            "debt_collection": "坏账催收数据",
            "legal_document": "法律文档",
            "contract": "合同文件",
            "other": "其他类型"
        },
        "max_file_size": "50MB",
        "max_files_per_upload": 10
    } 