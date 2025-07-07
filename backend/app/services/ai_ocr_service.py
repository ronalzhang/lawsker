"""
AI OCR服务 - 用于识别律师证、身份证等证件信息
支持多种OCR引擎：百度、腾讯、阿里云等
"""

import re
import json
import base64
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from PIL import Image
import io
import logging
from fastapi import HTTPException, UploadFile

# PIL/Pillow 图像处理相关配置已简化，避免版本兼容性问题

logger = logging.getLogger(__name__)

class AIDocumentOCRService:
    """AI文档识别服务"""
    
    def __init__(self):
        # 支持的OCR引擎配置
        self.ocr_engines = {
            'baidu': {
                'name': '百度OCR',
                'api_key': 'your_baidu_api_key',
                'secret_key': 'your_baidu_secret_key',
                'endpoint': 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
            },
            'tencent': {
                'name': '腾讯OCR',
                'secret_id': 'your_tencent_secret_id',
                'secret_key': 'your_tencent_secret_key',
                'endpoint': 'https://ocr.tencentcloudapi.com/'
            },
            'aliyun': {
                'name': '阿里云OCR',
                'access_key': 'your_aliyun_access_key',
                'access_secret': 'your_aliyun_access_secret',
                'endpoint': 'https://ocr-api.cn-hangzhou.aliyuncs.com'
            }
        }
        
        # 律师证信息提取规则
        self.lawyer_license_patterns = {
            'license_number': [
                r'执业证号[：:]?\s*([A-Z0-9]{10,20})',
                r'证号[：:]?\s*([A-Z0-9]{10,20})',
                r'执业证书编号[：:]?\s*([A-Z0-9]{10,20})'
            ],
            'name': [
                r'姓名[：:]?\s*([^\s]{2,10})',
                r'持证人[：:]?\s*([^\s]{2,10})',
                r'律师姓名[：:]?\s*([^\s]{2,10})'
            ],
            'gender': [
                r'性别[：:]?\s*([男女])',
                r'性别[：:]?\s*(男|女)'
            ],
            'id_card': [
                r'身份证号[：:]?\s*([0-9X]{15,18})',
                r'身份证[：:]?\s*([0-9X]{15,18})',
                r'证件号码[：:]?\s*([0-9X]{15,18})'
            ],
            'authority': [
                r'发证机关[：:]?\s*([^\n]{5,30})',
                r'颁发机关[：:]?\s*([^\n]{5,30})',
                r'发证单位[：:]?\s*([^\n]{5,30})'
            ],
            'issue_date': [
                r'发证日期[：:]?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
                r'颁发日期[：:]?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
                r'发证时间[：:]?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}-\d{1,2}-\d{1,2})',
                r'(\d{4}/\d{1,2}/\d{1,2})'
            ],
            'law_firm': [
                r'律师事务所[：:]?\s*([^\n]{5,50})',
                r'执业机构[：:]?\s*([^\n]{5,50})',
                r'所属律所[：:]?\s*([^\n]{5,50})'
            ]
        }
    
    async def extract_lawyer_license_info(self, image_file: UploadFile) -> Dict[str, Any]:
        """
        从律师证图片中提取信息
        """
        try:
            # 读取图片文件
            image_content = await image_file.read()
            
            # 验证图片格式
            if not self._validate_image_format(image_content):
                raise HTTPException(status_code=400, detail="不支持的图片格式")
            
            # 图片预处理
            processed_image = self._preprocess_image(image_content)
            
            # OCR识别
            ocr_result = await self._perform_ocr(processed_image)
            
            # 信息提取
            extracted_info = self._extract_lawyer_info(ocr_result)
            
            # 信息验证
            validation_result = self._validate_extracted_info(extracted_info)
            
            # 计算置信度
            confidence_score = self._calculate_confidence_score(extracted_info, validation_result)
            
            return {
                'success': True,
                'extracted_info': extracted_info,
                'validation_result': validation_result,
                'confidence_score': confidence_score,
                'ocr_raw_result': ocr_result,
                'extraction_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"律师证信息提取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extraction_timestamp': datetime.now().isoformat()
            }
    
    def _validate_image_format(self, image_content: bytes) -> bool:
        """验证图片格式"""
        try:
            image = Image.open(io.BytesIO(image_content))
            if image.format:
                return image.format.lower() in ['jpeg', 'jpg', 'png', 'bmp']
            return False
        except Exception:
            return False
    
    def _preprocess_image(self, image_content: bytes) -> bytes:
        """图片预处理：调整大小、增强对比度等"""
        try:
            image = Image.open(io.BytesIO(image_content))
            
            # 调整图片大小（如果太大）
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                # 使用默认重采样方法，避免版本兼容性问题
                image.thumbnail(max_size)
            
            # 转换为RGB格式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 保存处理后的图片
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"图片预处理失败，使用原图: {str(e)}")
            return image_content
    
    async def _perform_ocr(self, image_content: bytes) -> str:
        """执行OCR识别"""
        # 这里可以调用真实的OCR API
        # 为了演示，我们返回模拟的OCR结果
        return self._simulate_ocr_result()
    
    def _simulate_ocr_result(self) -> str:
        """模拟OCR识别结果"""
        return """
        中华人民共和国律师执业证
        
        姓名：漆红秀
        性别：女
        身份证号：511124198310174027
        执业证号：15101201011897330
        
        执业机构：四川科信律师事务所
        执业证类别：专职律师
        
        发证机关：四川省司法厅
        发证日期：2010年07月14日
        
        本证书是律师执业的法定证件
        """
    
    def _extract_lawyer_info(self, ocr_text: str) -> Dict[str, Any]:
        """从OCR结果中提取律师信息"""
        extracted_info = {}
        
        for field, patterns in self.lawyer_license_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, ocr_text)
                if match:
                    extracted_info[field] = match.group(1).strip()
                    break
        
        # 特殊处理日期格式
        if 'issue_date' in extracted_info:
            extracted_info['issue_date'] = self._parse_date(extracted_info['issue_date'])
        
        # 计算执业年限
        if 'issue_date' in extracted_info and extracted_info['issue_date']:
            try:
                issue_date = datetime.strptime(extracted_info['issue_date'], '%Y-%m-%d')
                years_of_practice = (datetime.now() - issue_date).days // 365
                extracted_info['years_of_practice'] = max(0, years_of_practice)
            except Exception:
                extracted_info['years_of_practice'] = 0
        
        return extracted_info
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串"""
        try:
            # 处理中文日期格式
            if '年' in date_str and '月' in date_str and '日' in date_str:
                date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
            
            # 尝试解析不同格式的日期
            date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d']
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def _validate_extracted_info(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证提取的信息"""
        validation_result = {
            'valid_fields': [],
            'invalid_fields': [],
            'warnings': []
        }
        
        # 验证律师证号
        if 'license_number' in extracted_info:
            license_number = extracted_info['license_number']
            if re.match(r'^[A-Z0-9]{10,20}$', license_number):
                validation_result['valid_fields'].append('license_number')
            else:
                validation_result['invalid_fields'].append('license_number')
                validation_result['warnings'].append('律师证号格式不正确')
        
        # 验证身份证号
        if 'id_card' in extracted_info:
            id_card = extracted_info['id_card']
            if self._validate_id_card(id_card):
                validation_result['valid_fields'].append('id_card')
            else:
                validation_result['invalid_fields'].append('id_card')
                validation_result['warnings'].append('身份证号格式不正确')
        
        # 验证姓名
        if 'name' in extracted_info:
            name = extracted_info['name']
            if 2 <= len(name) <= 10 and re.match(r'^[\u4e00-\u9fa5]+$', name):
                validation_result['valid_fields'].append('name')
            else:
                validation_result['invalid_fields'].append('name')
                validation_result['warnings'].append('姓名格式不正确')
        
        # 验证性别
        if 'gender' in extracted_info:
            gender = extracted_info['gender']
            if gender in ['男', '女']:
                validation_result['valid_fields'].append('gender')
            else:
                validation_result['invalid_fields'].append('gender')
                validation_result['warnings'].append('性别信息不正确')
        
        # 验证发证日期
        if 'issue_date' in extracted_info:
            issue_date = extracted_info['issue_date']
            if issue_date:
                try:
                    parsed_date = datetime.strptime(issue_date, '%Y-%m-%d')
                    if parsed_date <= datetime.now():
                        validation_result['valid_fields'].append('issue_date')
                    else:
                        validation_result['invalid_fields'].append('issue_date')
                        validation_result['warnings'].append('发证日期不能是未来日期')
                except ValueError:
                    validation_result['invalid_fields'].append('issue_date')
                    validation_result['warnings'].append('发证日期格式不正确')
        
        return validation_result
    
    def _validate_id_card(self, id_card: str) -> bool:
        """验证身份证号"""
        if not id_card:
            return False
        
        # 18位身份证号验证
        if len(id_card) == 18:
            return re.match(r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9X]$', id_card) is not None
        
        # 15位身份证号验证
        elif len(id_card) == 15:
            return re.match(r'^[1-9]\d{7}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}$', id_card) is not None
        
        return False
    
    def _calculate_confidence_score(self, extracted_info: Dict[str, Any], validation_result: Dict[str, Any]) -> int:
        """计算置信度分数"""
        total_fields = len(self.lawyer_license_patterns)
        extracted_fields = len(extracted_info)
        valid_fields = len(validation_result['valid_fields'])
        
        # 基础分数：提取字段数量
        base_score = (extracted_fields / total_fields) * 60
        
        # 验证分数：有效字段数量
        validation_score = (valid_fields / max(1, extracted_fields)) * 40
        
        # 总分
        total_score = int(base_score + validation_score)
        
        return min(100, max(0, total_score))
    
    def get_extraction_template(self) -> Dict[str, Any]:
        """获取信息提取模板"""
        return {
            'required_fields': [
                'license_number',  # 执业证号
                'name',           # 姓名
                'gender',         # 性别
                'id_card',        # 身份证号
                'authority',      # 发证机关
                'issue_date',     # 发证日期
                'law_firm'        # 律师事务所
            ],
            'optional_fields': [
                'years_of_practice',  # 执业年限
                'practice_areas',     # 执业领域
                'license_type'        # 执业类别
            ],
            'validation_rules': {
                'license_number': '10-20位字母数字组合',
                'name': '2-10个中文字符',
                'gender': '男或女',
                'id_card': '15或18位身份证号',
                'authority': '发证机关名称',
                'issue_date': 'YYYY-MM-DD格式日期',
                'law_firm': '律师事务所名称'
            }
        }
    
    async def batch_extract_lawyer_info(self, image_files: List[UploadFile]) -> List[Dict[str, Any]]:
        """批量提取律师证信息"""
        results = []
        
        for image_file in image_files:
            try:
                result = await self.extract_lawyer_license_info(image_file)
                results.append({
                    'filename': image_file.filename,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'filename': image_file.filename,
                    'result': {
                        'success': False,
                        'error': str(e)
                    }
                })
        
        return results 