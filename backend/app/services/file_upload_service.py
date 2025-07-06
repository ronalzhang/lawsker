"""
安全文件上传服务 - 简化版本
处理银行机构坏账数据上传
"""

import os
import uuid
import hashlib
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

# 尝试导入pandas，如果失败则使用替代方案
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

class FileUploadService:
    """安全文件上传服务"""
    
    # 允许的文件类型和大小限制
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv', '.pdf', '.doc', '.docx'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_FILES_PER_UPLOAD = 10
    
    def __init__(self):
        self.upload_dir = "/root/lawsker/uploads"
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {
            'excel': ['.xlsx', '.xls'],
            'csv': ['.csv'],
            'pdf': ['.pdf'],
            'word': ['.doc', '.docx']
        }
        self.allowed_mime_types = {
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
    
    def validate_file(self, file: UploadFile) -> bool:
        """验证文件类型和大小"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
            
        # 检查文件大小
        if file.size and file.size > self.max_file_size:
            raise HTTPException(status_code=400, detail="文件大小超过限制(50MB)")
        
        # 检查文件扩展名
        file_ext = os.path.splitext(file.filename)[1].lower()
        valid_extensions = []
        for ext_list in self.allowed_extensions.values():
            valid_extensions.extend(ext_list)
        
        if file_ext not in valid_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
        
        return True
    

    
    def check_malicious_content(self, file_content: bytes) -> bool:
        """检查恶意内容"""
        # 检查脚本注入
        dangerous_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'eval(',
            b'exec('
        ]
        
        content_lower = file_content.lower()
        for pattern in dangerous_patterns:
            if pattern in content_lower:
                raise HTTPException(status_code=400, detail="文件包含潜在恶意内容")
        
        return True
    
    def generate_safe_filename(self, original_filename: str) -> str:
        """生成安全的文件名"""
        # 获取文件扩展名
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        # 生成唯一标识符
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成文件内容哈希（用于防重复）
        content_hash = hashlib.sha256(f"{original_filename}{unique_id}{timestamp}".encode()).hexdigest()[:8]
        
        return f"{timestamp}_{content_hash}_{unique_id}{file_ext}"
    
    def create_upload_directory(self) -> str:
        """创建上传目录"""
        # 按日期创建目录结构
        date_dir = datetime.now().strftime("%Y/%m/%d")
        full_path = os.path.join(self.upload_dir, date_dir)
        
        os.makedirs(full_path, exist_ok=True)
        return full_path
    
    def validate_debt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证坏账数据格式和完整性"""
        required_fields = ['debtor_name', 'debtor_id', 'debtor_phone', 'amount', 'overdue_days']
        
        # 检查必需字段
        for field in required_fields:
            if field not in data or not data[field]:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        # 验证身份证号格式
        id_pattern = r'^\d{15}$|^\d{17}[\dXx]$'
        if not re.match(id_pattern, str(data['debtor_id'])):
            raise HTTPException(status_code=400, detail="身份证号格式错误")
        
        # 验证主要联系电话格式
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, str(data['debtor_phone'])):
            raise HTTPException(status_code=400, detail="债务人电话格式错误")
        
        # 验证并处理多个联系人电话
        contact_phones = []
        
        # 添加债务人电话
        contact_phones.append(str(data['debtor_phone']))
        
        # 处理亲属电话（可能有多个，用逗号分隔）
        if 'relative_phones' in data and data['relative_phones']:
            relative_phones = str(data['relative_phones']).split(',')
            for phone in relative_phones:
                phone = phone.strip()
                if phone and re.match(phone_pattern, phone):
                    contact_phones.append(phone)
        
        # 处理紧急联系人电话（可能有多个，用逗号分隔）
        if 'emergency_phones' in data and data['emergency_phones']:
            emergency_phones = str(data['emergency_phones']).split(',')
            for phone in emergency_phones:
                phone = phone.strip()
                if phone and re.match(phone_pattern, phone):
                    contact_phones.append(phone)
        
        # 处理其他联系人电话
        if 'other_phones' in data and data['other_phones']:
            other_phones = str(data['other_phones']).split(',')
            for phone in other_phones:
                phone = phone.strip()
                if phone and re.match(phone_pattern, phone):
                    contact_phones.append(phone)
        
        # 添加担保人电话
        if 'guarantor_phone' in data and data['guarantor_phone']:
            guarantor_phone = str(data['guarantor_phone']).strip()
            if guarantor_phone and re.match(phone_pattern, guarantor_phone):
                contact_phones.append(guarantor_phone)
        
        # 去重并保存所有有效电话
        unique_phones = list(set(contact_phones))
        data['all_contact_phones'] = ','.join(unique_phones)
        data['total_phones'] = len(unique_phones)
        
        # 验证金额
        try:
            amount = float(data['amount'])
            if amount <= 0:
                raise HTTPException(status_code=400, detail="金额必须大于0")
            data['amount'] = amount
        except ValueError:
            raise HTTPException(status_code=400, detail="金额格式错误")
        
        # 验证逾期天数
        try:
            overdue_days = int(data['overdue_days'])
            if overdue_days < 0:
                raise HTTPException(status_code=400, detail="逾期天数不能为负数")
            data['overdue_days'] = overdue_days
        except ValueError:
            raise HTTPException(status_code=400, detail="逾期天数格式错误")
        
        return data
    
    def process_excel_data(self, file_path: str, data_type: str) -> List[Dict[str, Any]]:
        """处理Excel数据"""
        if not HAS_PANDAS:
            raise HTTPException(status_code=500, detail="系统不支持Excel文件处理")
            
        try:
            df = pd.read_excel(file_path)
            
            if data_type == 'debt_collection':
                # 处理坏账催收数据
                processed_data = []
                for _, row in df.iterrows():
                    row_data = {
                        'debtor_name': row.get('债务人姓名', ''),
                        'debtor_id': row.get('身份证号', ''),
                        'debtor_phone': row.get('债务人电话', ''),
                        'relative_phones': row.get('亲属电话', ''),  # 支持多个电话，逗号分隔
                        'emergency_phones': row.get('紧急联系人电话', ''),  # 支持多个电话，逗号分隔
                        'other_phones': row.get('其他联系人电话', ''),  # 支持多个电话，逗号分隔
                        'amount': row.get('欠款金额', 0),
                        'overdue_days': row.get('逾期天数', 0),
                        'bank_name': row.get('银行名称', ''),
                        'loan_type': row.get('贷款类型', ''),
                        'contract_number': row.get('合同编号', ''),
                        'last_payment_date': row.get('最后还款日期', ''),
                        'debtor_address': row.get('债务人地址', ''),
                        'workplace': row.get('工作单位', ''),
                        'monthly_income': row.get('月收入', 0),
                        'guarantor_name': row.get('担保人姓名', ''),
                        'guarantor_phone': row.get('担保人电话', ''),
                        'remarks': row.get('备注', '')
                    }
                    
                    # 验证数据
                    validated_data = self.validate_debt_data(row_data)
                    processed_data.append(validated_data)
                
                return processed_data
            
            return []
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel文件处理失败: {str(e)}")
    
    def process_csv_data(self, file_path: str, data_type: str) -> List[Dict[str, Any]]:
        """处理CSV数据"""
        if not HAS_PANDAS:
            raise HTTPException(status_code=500, detail="系统不支持CSV文件处理")
            
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            if data_type == 'debt_collection':
                # 处理坏账催收数据
                processed_data = []
                for _, row in df.iterrows():
                    row_data = {
                        'debtor_name': row.get('债务人姓名', ''),
                        'debtor_id': row.get('身份证号', ''),
                        'debtor_phone': row.get('债务人电话', ''),
                        'relative_phones': row.get('亲属电话', ''),
                        'emergency_phones': row.get('紧急联系人电话', ''),
                        'other_phones': row.get('其他联系人电话', ''),
                        'amount': row.get('欠款金额', 0),
                        'overdue_days': row.get('逾期天数', 0),
                        'bank_name': row.get('银行名称', ''),
                        'loan_type': row.get('贷款类型', ''),
                        'contract_number': row.get('合同编号', ''),
                        'last_payment_date': row.get('最后还款日期', ''),
                        'debtor_address': row.get('债务人地址', ''),
                        'workplace': row.get('工作单位', ''),
                        'monthly_income': row.get('月收入', 0),
                        'guarantor_name': row.get('担保人姓名', ''),
                        'guarantor_phone': row.get('担保人电话', ''),
                        'remarks': row.get('备注', '')
                    }
                    
                    # 验证数据
                    validated_data = self.validate_debt_data(row_data)
                    processed_data.append(validated_data)
                
                return processed_data
            
            return []
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"CSV文件处理失败: {str(e)}")
    
    async def upload_file(self, file: UploadFile, data_type: str, user_id: int) -> Dict[str, Any]:
        """上传文件"""
        try:
            # 验证文件
            self.validate_file(file)
            
            # 读取文件内容
            file_content = await file.read()
            
            # 检查恶意内容
            self.check_malicious_content(file_content)
            
            # 创建上传目录
            upload_path = self.create_upload_directory()
            
            # 生成安全文件名 - 确保filename不为None
            if not file.filename:
                raise HTTPException(status_code=400, detail="文件名不能为空")
            
            safe_filename = self.generate_safe_filename(file.filename)
            file_path = os.path.join(upload_path, safe_filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # 设置文件权限
            os.chmod(file_path, 0o644)
            
            # 处理文件数据
            processed_data = []
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                processed_data = self.process_excel_data(file_path, data_type)
            elif file_ext == '.csv':
                processed_data = self.process_csv_data(file_path, data_type)
            
            return {
                "filename": file.filename,
                "safe_filename": safe_filename,
                "file_size": len(file_content),
                "data_type": data_type,
                "processed_records": len(processed_data),
                "processed_data": processed_data[:10] if processed_data else [],  # 返回前10条预览
                "total_records": len(processed_data),
                "upload_time": datetime.now(),
                "message": "文件上传成功"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    def get_supported_types(self) -> Dict[str, Any]:
        """获取支持的文件类型和数据类型"""
        return {
            "file_types": {
                "excel": {
                    "extensions": self.allowed_extensions['excel'],
                    "description": "Excel电子表格文件",
                    "max_size": "50MB"
                },
                "csv": {
                    "extensions": self.allowed_extensions['csv'],
                    "description": "CSV逗号分隔值文件",
                    "max_size": "50MB"
                },
                "pdf": {
                    "extensions": self.allowed_extensions['pdf'],
                    "description": "PDF文档文件",
                    "max_size": "50MB"
                },
                "word": {
                    "extensions": self.allowed_extensions['word'],
                    "description": "Word文档文件",
                    "max_size": "50MB"
                }
            },
            "data_types": {
                "debt_collection": {
                    "name": "坏账催收数据",
                    "description": "银行机构坏账业务数据",
                    "required_fields": [
                        "债务人姓名", "身份证号", "债务人电话", "欠款金额", "逾期天数"
                    ],
                    "optional_fields": [
                        "亲属电话", "紧急联系人电话", "其他联系人电话", "银行名称", "贷款类型", 
                        "合同编号", "最后还款日期", "债务人地址", "工作单位", "月收入", 
                        "担保人姓名", "担保人电话", "备注"
                    ],
                    "contact_phone_fields": {
                        "debtor_phone": "债务人电话（必填）",
                        "relative_phones": "亲属电话（可选，多个用逗号分隔）",
                        "emergency_phones": "紧急联系人电话（可选，多个用逗号分隔）",
                        "other_phones": "其他联系人电话（可选，多个用逗号分隔）",
                        "guarantor_phone": "担保人电话（可选）"
                    },
                    "sms_integration": {
                        "description": "系统将自动提取所有有效的联系人电话，用于律师函短信群发",
                        "phone_validation": "所有电话号码必须符合中国大陆手机号格式",
                        "deduplication": "系统自动去重相同的电话号码"
                    }
                },
                "legal_documents": {
                    "name": "法律文档",
                    "description": "合同、协议等法律文件"
                },
                "contracts": {
                    "name": "合同文件",
                    "description": "各类合同文档"
                },
                "others": {
                    "name": "其他文件",
                    "description": "其他类型的业务文件"
                }
            }
        } 