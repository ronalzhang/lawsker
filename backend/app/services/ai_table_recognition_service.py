"""
AI智能表格识别服务
自动识别用户上传的任意格式表格，转换为标准的债务催收数据格式
"""

import os
import json
import re
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from fastapi import HTTPException, UploadFile
from datetime import datetime
import logging

# 尝试导入AI服务
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# 尝试导入pandas和openpyxl
try:
    import pandas as pd
    import openpyxl
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

logger = logging.getLogger(__name__)

class AITableRecognitionService:
    """AI智能表格识别服务"""
    
    def __init__(self, config_service=None):
        """初始化AI表格识别服务"""
        self.config_service = config_service
        
        # 标准债务催收数据字段映射
        self.standard_fields = {
            'debtor_name': ['债务人姓名', '姓名', '客户姓名', '借款人', '用户姓名', '债务人名称', '客户名称'],
            'debtor_id': ['身份证号', '证件号码', '身份证', 'ID号', '证件号', '客户身份证', '身份证号码'],
            'debtor_phone': ['债务人电话', '手机号', '电话', '联系电话', '债务人手机', '主要电话', '联系方式'],
            'relative_phones': ['亲属电话', '家属电话', '亲人电话', '家庭电话', '联系人电话', '紧急联系人'],
            'emergency_phones': ['紧急联系人电话', '紧急电话', '应急联系人', '紧急联系方式'],
            'other_phones': ['其他联系人电话', '备用电话', '其他电话', '第二联系人', '备用联系方式'],
            'amount': ['欠款金额', '借款金额', '贷款金额', '债务金额', '本金', '借款本金', '逾期金额'],
            'overdue_days': ['逾期天数', '逾期日数', '超期天数', '违约天数', '拖欠天数'],
            'bank_name': ['银行名称', '贷款银行', '放贷机构', '金融机构', '银行', '机构名称'],
            'loan_type': ['贷款类型', '借款类型', '产品类型', '业务类型', '贷款产品'],
            'contract_number': ['合同编号', '协议编号', '合同号', '协议号', '借款合同号', '贷款合同号'],
            'last_payment_date': ['最后还款日期', '最后付款日', '最后还款时间', '上次还款日'],
            'debtor_address': ['债务人地址', '联系地址', '家庭住址', '居住地址', '客户地址'],
            'workplace': ['工作单位', '就职单位', '公司名称', '雇主', '工作地点'],
            'monthly_income': ['月收入', '月薪', '工资', '收入', '月收入水平'],
            'guarantor_name': ['担保人姓名', '担保人', '保证人', '担保人名称'],
            'guarantor_phone': ['担保人电话', '担保人手机', '保证人电话', '担保人联系方式'],
            'remarks': ['备注', '说明', '其他信息', '补充说明', '备注信息']
        }
        
        # 必填字段
        self.required_fields = ['debtor_name', 'debtor_id', 'debtor_phone', 'amount', 'overdue_days']
        
        # 支持的文件格式
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        
    async def recognize_and_convert_table(self, file: UploadFile, data_type: str = 'debt_collection') -> Dict[str, Any]:
        """
        识别并转换表格数据
        
        Args:
            file: 上传的文件
            data_type: 数据类型，默认为债务催收
            
        Returns:
            转换结果包含识别状态、数据、建议等
        """
        try:
            # 验证文件格式
            if not file.filename:
                raise HTTPException(status_code=400, detail="文件名不能为空")
                
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'不支持的文件格式 {file_ext}',
                    'supported_formats': self.supported_formats,
                    'suggestion': '请使用Excel (.xlsx, .xls) 或 CSV (.csv) 格式'
                }
            
            # 读取文件内容
            file_content = await file.read()
            
            # 解析表格数据
            if file_ext in ['.xlsx', '.xls']:
                raw_data = await self._parse_excel_data(file_content)
            elif file_ext == '.csv':
                raw_data = await self._parse_csv_data(file_content)
            else:
                raise HTTPException(status_code=400, detail="不支持的文件格式")
            
            if not raw_data or len(raw_data) == 0:
                return {
                    'success': False,
                    'error': '表格数据为空或无法解析',
                    'suggestion': '请检查文件是否包含有效数据'
                }
            
            # AI智能字段映射
            mapping_result = await self._ai_field_mapping(raw_data)
            
            if not mapping_result['success']:
                return {
                    'success': False,
                    'error': mapping_result['error'],
                    'raw_data_preview': raw_data[:3],  # 返回前3行数据供参考
                    'suggestion': '建议下载标准模板重新填写'
                }
            
            # 转换数据格式
            converted_data = await self._convert_to_standard_format(
                raw_data, mapping_result['field_mapping']
            )
            
            # 数据验证
            validation_result = await self._validate_converted_data(converted_data)
            
            return {
                'success': True,
                'message': f'成功识别并转换 {len(converted_data)} 条记录',
                'original_filename': file.filename,
                'converted_data': converted_data,
                'field_mapping': mapping_result['field_mapping'],
                'validation_result': validation_result,
                'statistics': {
                    'total_records': len(converted_data),
                    'valid_records': validation_result['valid_count'],
                    'invalid_records': validation_result['invalid_count'],
                    'success_rate': f"{validation_result['valid_count']/len(converted_data)*100:.1f}%"
                },
                'ai_confidence': mapping_result.get('confidence', 0),
                'processing_notes': mapping_result.get('notes', '')
            }
            
        except Exception as e:
            logger.error(f"AI表格识别失败: {str(e)}")
            return {
                'success': False,
                'error': f'表格识别处理失败: {str(e)}',
                'suggestion': '请检查文件格式或尝试使用标准模板'
            }
    
    async def _parse_excel_data(self, file_content: bytes) -> List[Dict[str, Any]]:
        """解析Excel文件数据"""
        if not HAS_PANDAS:
            raise HTTPException(status_code=500, detail="系统不支持Excel文件处理")
        
        try:
            # 使用pandas读取Excel
            import io
            df = pd.read_excel(io.BytesIO(file_content))
            
            # 转换为字典列表
            data = df.to_dict('records')
            
            # 清理空值和无效行
            cleaned_data = []
            for row in data:
                # 过滤掉所有值都为空的行
                if any(pd.notna(value) and str(value).strip() for value in row.values()):
                    # 清理每个字段的值
                    cleaned_row = {}
                    for key, value in row.items():
                        if pd.notna(value):
                            cleaned_row[str(key).strip()] = str(value).strip()
                        else:
                            cleaned_row[str(key).strip()] = ''
                    cleaned_data.append(cleaned_row)
            
            return cleaned_data
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel文件解析失败: {str(e)}")
    
    async def _parse_csv_data(self, file_content: bytes) -> List[Dict[str, Any]]:
        """解析CSV文件数据"""
        if not HAS_PANDAS:
            raise HTTPException(status_code=500, detail="系统不支持CSV文件处理")
        
        try:
            # 尝试不同编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            df = None
            
            for encoding in encodings:
                try:
                    import io
                    df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise HTTPException(status_code=400, detail="CSV文件编码不支持")
            
            # 转换为字典列表
            data = df.to_dict('records')
            
            # 清理数据
            cleaned_data = []
            for row in data:
                if any(pd.notna(value) and str(value).strip() for value in row.values()):
                    cleaned_row = {}
                    for key, value in row.items():
                        if pd.notna(value):
                            cleaned_row[str(key).strip()] = str(value).strip()
                        else:
                            cleaned_row[str(key).strip()] = ''
                    cleaned_data.append(cleaned_row)
            
            return cleaned_data
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"CSV文件解析失败: {str(e)}")
    
    async def _ai_field_mapping(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """AI智能字段映射"""
        try:
            if not raw_data:
                return {'success': False, 'error': '没有数据需要映射'}
            
            # 获取原始字段列表
            original_fields = list(raw_data[0].keys()) if raw_data else []
            
            if not original_fields:
                return {'success': False, 'error': '无法获取表格字段'}
            
            # 首先尝试规则匹配
            rule_mapping = self._rule_based_mapping(original_fields)
            
            # 如果规则匹配成功率高，直接使用
            if rule_mapping['confidence'] >= 0.8:
                return {
                    'success': True,
                    'field_mapping': rule_mapping['mapping'],
                    'confidence': rule_mapping['confidence'],
                    'method': 'rule_based',
                    'notes': '基于规则成功映射字段'
                }
            
            # 否则尝试AI映射（如果可用）
            if HAS_OPENAI and self.config_service:
                ai_mapping = await self._ai_based_mapping(original_fields, raw_data[:3])
                if ai_mapping['success']:
                    return ai_mapping
            
            # AI不可用时，使用改进的规则映射
            enhanced_mapping = self._enhanced_rule_mapping(original_fields, raw_data[:5])
            
            return {
                'success': enhanced_mapping['confidence'] >= 0.5,
                'field_mapping': enhanced_mapping['mapping'],
                'confidence': enhanced_mapping['confidence'],
                'method': 'enhanced_rule',
                'notes': f"字段映射完成，置信度: {enhanced_mapping['confidence']:.1%}",
                'error': '部分字段无法自动映射' if enhanced_mapping['confidence'] < 0.8 else None
            }
            
        except Exception as e:
            logger.error(f"字段映射失败: {str(e)}")
            return {
                'success': False,
                'error': f'字段映射失败: {str(e)}'
            }
    
    def _rule_based_mapping(self, original_fields: List[str]) -> Dict[str, Any]:
        """基于规则的字段映射"""
        mapping = {}
        confidence_scores = []
        
        for standard_field, possible_names in self.standard_fields.items():
            best_match = None
            best_score = 0
            
            for original_field in original_fields:
                # 直接匹配
                if original_field in possible_names:
                    best_match = original_field
                    best_score = 1.0
                    break
                
                # 模糊匹配
                for possible_name in possible_names:
                    if possible_name in original_field or original_field in possible_name:
                        score = 0.8
                        if score > best_score:
                            best_match = original_field
                            best_score = score
            
            if best_match:
                mapping[standard_field] = best_match
                confidence_scores.append(best_score)
        
        # 计算总体置信度
        overall_confidence = sum(confidence_scores) / len(self.standard_fields) if confidence_scores else 0
        
        return {
            'mapping': mapping,
            'confidence': overall_confidence
        }
    
    def _enhanced_rule_mapping(self, original_fields: List[str], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """增强的规则映射，结合数据内容分析"""
        mapping = {}
        confidence_scores = []
        
        # 基础规则映射
        base_mapping = self._rule_based_mapping(original_fields)
        mapping.update(base_mapping['mapping'])
        
        # 数据内容分析增强
        for original_field in original_fields:
            if original_field in mapping.values():
                continue  # 已经映射的字段跳过
            
            # 分析字段内容特征
            field_analysis = self._analyze_field_content(original_field, sample_data)
            
            if field_analysis['suggested_mapping']:
                standard_field = field_analysis['suggested_mapping']
                if standard_field not in mapping:
                    mapping[standard_field] = original_field
                    confidence_scores.append(field_analysis['confidence'])
        
        # 计算置信度
        required_mapped = sum(1 for field in self.required_fields if field in mapping)
        required_ratio = required_mapped / len(self.required_fields)
        
        total_mapped = len(mapping)
        total_ratio = total_mapped / len(self.standard_fields)
        
        overall_confidence = (required_ratio * 0.7 + total_ratio * 0.3)
        
        return {
            'mapping': mapping,
            'confidence': overall_confidence
        }
    
    def _analyze_field_content(self, field_name: str, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析字段内容特征"""
        if not sample_data:
            return {'suggested_mapping': None, 'confidence': 0}
        
        # 获取该字段的样本值
        sample_values = []
        for row in sample_data:
            value = row.get(field_name, '')
            if value and str(value).strip():
                sample_values.append(str(value).strip())
        
        if not sample_values:
            return {'suggested_mapping': None, 'confidence': 0}
        
        # 身份证号码识别
        id_pattern = r'^\d{15}$|^\d{17}[\dXx]$'
        if all(re.match(id_pattern, value) for value in sample_values):
            return {'suggested_mapping': 'debtor_id', 'confidence': 0.9}
        
        # 手机号码识别
        phone_pattern = r'^1[3-9]\d{9}$'
        if all(re.match(phone_pattern, value) for value in sample_values):
            return {'suggested_mapping': 'debtor_phone', 'confidence': 0.9}
        
        # 金额识别
        if all(self._is_amount(value) for value in sample_values):
            return {'suggested_mapping': 'amount', 'confidence': 0.8}
        
        # 天数识别
        if all(value.isdigit() and 0 <= int(value) <= 3650 for value in sample_values):
            return {'suggested_mapping': 'overdue_days', 'confidence': 0.7}
        
        # 姓名识别（中文姓名2-4个字符）
        name_pattern = r'^[\u4e00-\u9fa5]{2,4}$'
        if all(re.match(name_pattern, value) for value in sample_values):
            return {'suggested_mapping': 'debtor_name', 'confidence': 0.7}
        
        return {'suggested_mapping': None, 'confidence': 0}
    
    def _is_amount(self, value: str) -> bool:
        """判断是否为金额"""
        try:
            # 移除常见的货币符号和逗号
            clean_value = value.replace('¥', '').replace(',', '').replace('￥', '')
            float(clean_value)
            return True
        except ValueError:
            return False
    
    async def _ai_based_mapping(self, original_fields: List[str], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于AI的字段映射"""
        try:
            # 构建AI提示
            prompt = self._build_ai_mapping_prompt(original_fields, sample_data)
            
            # 调用AI服务
            ai_config = await self.config_service.get_ai_config()
            openai.api_key = ai_config.get('openai_api_key')
            openai.base_url = ai_config.get('openai_base_url', 'https://api.openai.com/v1')
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的数据分析师，专门帮助用户映射表格字段到标准格式。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            # 解析AI响应
            ai_response = response.choices[0].message.content
            mapping_result = self._parse_ai_mapping_response(ai_response)
            
            return {
                'success': True,
                'field_mapping': mapping_result['mapping'],
                'confidence': mapping_result['confidence'],
                'method': 'ai_based',
                'notes': f"AI映射完成，置信度: {mapping_result['confidence']:.1%}"
            }
            
        except Exception as e:
            logger.error(f"AI字段映射失败: {str(e)}")
            return {
                'success': False,
                'error': f'AI映射失败: {str(e)}'
            }
    
    def _build_ai_mapping_prompt(self, original_fields: List[str], sample_data: List[Dict[str, Any]]) -> str:
        """构建AI映射提示"""
        prompt = f"""
请将以下原始表格字段映射到我们的标准债务催收数据字段。

原始字段：{original_fields}

标准字段定义：
{json.dumps(self.standard_fields, ensure_ascii=False, indent=2)}

样本数据：
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

请返回JSON格式的映射结果，格式如下：
{{
    "mapping": {{
        "标准字段名": "原始字段名"
    }},
    "confidence": 0.85,
    "notes": "映射说明"
}}

要求：
1. 只映射有把握的字段
2. 置信度应该反映映射的准确性
3. 必填字段：{self.required_fields}
"""
        return prompt
    
    def _parse_ai_mapping_response(self, response: str) -> Dict[str, Any]:
        """解析AI映射响应"""
        try:
            # 尝试解析JSON
            result = json.loads(response)
            return {
                'mapping': result.get('mapping', {}),
                'confidence': result.get('confidence', 0.5)
            }
        except json.JSONDecodeError:
            # 如果不是标准JSON，尝试简单解析
            return {
                'mapping': {},
                'confidence': 0.3
            }
    
    async def _convert_to_standard_format(self, raw_data: List[Dict[str, Any]], field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """转换为标准格式"""
        converted_data = []
        
        for row in raw_data:
            converted_row = {}
            
            # 按照映射转换字段
            for standard_field, original_field in field_mapping.items():
                value = row.get(original_field, '')
                converted_row[standard_field] = self._clean_field_value(standard_field, value)
            
            # 确保所有标准字段都存在
            for standard_field in self.standard_fields.keys():
                if standard_field not in converted_row:
                    converted_row[standard_field] = ''
            
            converted_data.append(converted_row)
        
        return converted_data
    
    def _clean_field_value(self, field_name: str, value: str) -> str:
        """清理字段值"""
        if not value:
            return ''
        
        value = str(value).strip()
        
        # 金额字段处理
        if field_name == 'amount':
            # 移除货币符号和逗号
            value = value.replace('¥', '').replace(',', '').replace('￥', '')
            try:
                # 验证是否为有效数字
                float(value)
                return value
            except ValueError:
                return ''
        
        # 电话号码字段处理
        if 'phone' in field_name:
            # 移除非数字字符
            value = re.sub(r'[^\d]', '', value)
            if len(value) == 11 and value.startswith('1'):
                return value
            return ''
        
        # 身份证号码处理
        if field_name == 'debtor_id':
            value = value.upper()
            if re.match(r'^\d{15}$|^\d{17}[\dX]$', value):
                return value
            return ''
        
        # 逾期天数处理
        if field_name == 'overdue_days':
            try:
                days = int(float(value))
                return str(max(0, days))  # 确保不是负数
            except ValueError:
                return ''
        
        return value
    
    async def _validate_converted_data(self, converted_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证转换后的数据"""
        validation_result = {
            'valid_count': 0,
            'invalid_count': 0,
            'errors': [],
            'warnings': []
        }
        
        for i, row in enumerate(converted_data):
            row_errors = []
            row_warnings = []
            
            # 检查必填字段
            for required_field in self.required_fields:
                if not row.get(required_field):
                    row_errors.append(f"缺少必填字段: {required_field}")
            
            # 验证数据格式
            if row.get('debtor_id') and not re.match(r'^\d{15}$|^\d{17}[\dX]$', row['debtor_id']):
                row_errors.append("身份证号格式错误")
            
            if row.get('debtor_phone') and not re.match(r'^1[3-9]\d{9}$', row['debtor_phone']):
                row_errors.append("债务人电话格式错误")
            
            if row.get('amount'):
                try:
                    amount = float(row['amount'])
                    if amount <= 0:
                        row_errors.append("金额必须大于0")
                except ValueError:
                    row_errors.append("金额格式错误")
            
            # 检查逾期天数
            if row.get('overdue_days'):
                try:
                    days = int(row['overdue_days'])
                    if days < 0:
                        row_errors.append("逾期天数不能为负数")
                except ValueError:
                    row_errors.append("逾期天数格式错误")
            
            # 统计结果
            if row_errors:
                validation_result['invalid_count'] += 1
                validation_result['errors'].append({
                    'row': i + 1,
                    'errors': row_errors
                })
            else:
                validation_result['valid_count'] += 1
            
            if row_warnings:
                validation_result['warnings'].append({
                    'row': i + 1,
                    'warnings': row_warnings
                })
        
        return validation_result
    
    def get_standard_template(self) -> Dict[str, Any]:
        """获取标准模板"""
        return {
            'template_name': '债务催收数据标准模板',
            'version': '1.0',
            'required_fields': self.required_fields,
            'all_fields': self.standard_fields,
            'sample_data': [
                {
                    '债务人姓名': '张三',
                    '身份证号': '110101199001011234',
                    '债务人电话': '13800138000',
                    '亲属电话': '13900139000,13700137000',
                    '欠款金额': '50000',
                    '逾期天数': '60',
                    '银行名称': '某某银行',
                    '贷款类型': '个人消费贷',
                    '合同编号': 'HT202401001',
                    '债务人地址': '北京市朝阳区XXX',
                    '工作单位': '某科技公司',
                    '月收入': '8000',
                    '备注': '优质客户'
                }
            ],
            'field_descriptions': {
                '债务人姓名': '债务人的真实姓名（必填）',
                '身份证号': '18位身份证号码（必填）',
                '债务人电话': '债务人手机号（必填）',
                '亲属电话': '多个电话用逗号分隔（可选）',
                '欠款金额': '欠款金额，数字格式（必填）',
                '逾期天数': '逾期天数，整数（必填）',
                '银行名称': '放贷机构名称（可选）',
                '贷款类型': '贷款产品类型（可选）',
                '合同编号': '借款合同编号（可选）',
                '债务人地址': '债务人联系地址（可选）',
                '工作单位': '债务人工作单位（可选）',
                '月收入': '债务人月收入（可选）',
                '备注': '其他补充信息（可选）'
            }
        } 