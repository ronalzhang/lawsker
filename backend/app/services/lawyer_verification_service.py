import re
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

class LawyerVerificationService:
    def __init__(self):
        # 律师证号码格式验证
        self.license_pattern = r'^[A-Z0-9]{10,20}$'
        
        # 支持的律师信息验证API
        self.verification_apis = {
            'china_lawyer_association': 'https://www.acla.org.cn/api/lawyer/verify',
            'local_bar_association': 'https://api.localbar.org/verify'
        }
    
    def validate_lawyer_info(self, lawyer_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证律师基本信息"""
        required_fields = ['name', 'law_firm', 'license_number', 'practice_area']
        
        # 检查必需字段
        for field in required_fields:
            if field not in lawyer_data or not lawyer_data[field]:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        # 验证律师姓名格式
        name = lawyer_data['name'].strip()
        if len(name) < 2 or len(name) > 10:
            raise HTTPException(status_code=400, detail="律师姓名长度应在2-10个字符之间")
        
        # 验证律师证号格式
        license_number = lawyer_data['license_number'].strip().upper()
        if not re.match(self.license_pattern, license_number):
            raise HTTPException(status_code=400, detail="律师证号格式错误")
        
        # 验证律所名称
        law_firm = lawyer_data['law_firm'].strip()
        if len(law_firm) < 5 or len(law_firm) > 50:
            raise HTTPException(status_code=400, detail="律所名称长度应在5-50个字符之间")
        
        # 验证执业领域
        practice_areas = lawyer_data['practice_area'].split(',')
        valid_areas = [
            '民商事诉讼', '刑事辩护', '公司法务', '知识产权', '劳动争议',
            '房地产', '金融证券', '行政诉讼', '婚姻家庭', '交通事故',
            '医疗纠纷', '建筑工程', '合同纠纷', '债权债务', '其他'
        ]
        
        for area in practice_areas:
            area = area.strip()
            if area not in valid_areas:
                raise HTTPException(status_code=400, detail=f"不支持的执业领域: {area}")
        
        # 验证联系方式
        if 'phone' in lawyer_data and lawyer_data['phone']:
            phone_pattern = r'^1[3-9]\d{9}$'
            if not re.match(phone_pattern, str(lawyer_data['phone'])):
                raise HTTPException(status_code=400, detail="手机号格式错误")
        
        if 'email' in lawyer_data and lawyer_data['email']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, lawyer_data['email']):
                raise HTTPException(status_code=400, detail="邮箱格式错误")
        
        return {
            'name': name,
            'law_firm': law_firm,
            'license_number': license_number,
            'practice_area': lawyer_data['practice_area'],
            'phone': lawyer_data.get('phone', ''),
            'email': lawyer_data.get('email', ''),
            'years_of_practice': lawyer_data.get('years_of_practice', 0),
            'education': lawyer_data.get('education', ''),
            'specialization': lawyer_data.get('specialization', ''),
            'verified': False,
            'verification_status': 'pending'
        }
    
    def verify_license_online(self, license_number: str, name: str) -> Dict[str, Any]:
        """在线验证律师证"""
        verification_result = {
            'verified': False,
            'source': '',
            'details': {},
            'error': ''
        }
        
        # 模拟API调用（实际应用中需要接入真实的律师协会API）
        try:
            # 这里可以接入多个验证源
            for api_name, api_url in self.verification_apis.items():
                try:
                    # 模拟API调用
                    response = self._simulate_api_call(api_name, license_number, name)
                    
                    if response['success']:
                        verification_result['verified'] = True
                        verification_result['source'] = api_name
                        verification_result['details'] = response['data']
                        break
                        
                except Exception as e:
                    verification_result['error'] = f"API调用失败: {str(e)}"
                    continue
            
            return verification_result
            
        except Exception as e:
            verification_result['error'] = f"验证过程出错: {str(e)}"
            return verification_result
    
    def _simulate_api_call(self, api_name: str, license_number: str, name: str) -> Dict[str, Any]:
        """模拟API调用（实际应用中替换为真实API）"""
        # 这是一个模拟的验证结果
        # 实际应用中需要调用真实的律师协会API
        
        # 模拟一些验证逻辑
        if len(license_number) >= 10 and len(name) >= 2:
            return {
                'success': True,
                'data': {
                    'name': name,
                    'license_number': license_number,
                    'status': 'active',
                    'issue_date': '2020-01-01',
                    'law_firm': '示例律师事务所',
                    'practice_area': '民商事诉讼',
                    'verified_at': datetime.now().isoformat()
                }
            }
        else:
            return {
                'success': False,
                'error': '律师信息验证失败'
            }
    
    def check_lawyer_qualification(self, lawyer_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查律师资格"""
        qualification_check = {
            'qualified': False,
            'score': 0,
            'requirements_met': [],
            'requirements_missing': [],
            'recommendations': []
        }
        
        score = 0
        
        # 基本信息完整性 (30分)
        if lawyer_data.get('name') and lawyer_data.get('law_firm') and lawyer_data.get('license_number'):
            score += 30
            qualification_check['requirements_met'].append('基本信息完整')
        else:
            qualification_check['requirements_missing'].append('基本信息不完整')
        
        # 执业年限 (20分)
        years_of_practice = lawyer_data.get('years_of_practice', 0)
        if years_of_practice >= 5:
            score += 20
            qualification_check['requirements_met'].append('执业经验丰富')
        elif years_of_practice >= 2:
            score += 10
            qualification_check['requirements_met'].append('有一定执业经验')
        else:
            qualification_check['requirements_missing'].append('执业经验不足')
            qualification_check['recommendations'].append('建议积累更多执业经验')
        
        # 专业领域匹配 (20分)
        practice_area = lawyer_data.get('practice_area', '')
        if '债权债务' in practice_area or '民商事诉讼' in practice_area:
            score += 20
            qualification_check['requirements_met'].append('专业领域匹配')
        elif '合同纠纷' in practice_area or '公司法务' in practice_area:
            score += 15
            qualification_check['requirements_met'].append('专业领域相关')
        else:
            qualification_check['requirements_missing'].append('专业领域不够匹配')
            qualification_check['recommendations'].append('建议加强债权债务相关业务经验')
        
        # 联系方式完整性 (15分)
        if lawyer_data.get('phone') and lawyer_data.get('email'):
            score += 15
            qualification_check['requirements_met'].append('联系方式完整')
        elif lawyer_data.get('phone') or lawyer_data.get('email'):
            score += 10
            qualification_check['requirements_met'].append('有基本联系方式')
        else:
            qualification_check['requirements_missing'].append('缺少联系方式')
        
        # 学历背景 (15分)
        education = lawyer_data.get('education', '')
        if '法学硕士' in education or '法律硕士' in education:
            score += 15
            qualification_check['requirements_met'].append('学历背景优秀')
        elif '法学学士' in education or '法律' in education:
            score += 10
            qualification_check['requirements_met'].append('有法学背景')
        else:
            qualification_check['recommendations'].append('建议提供学历背景信息')
        
        qualification_check['score'] = score
        qualification_check['qualified'] = score >= 70
        
        return qualification_check
    
    def get_verification_suggestions(self) -> Dict[str, Any]:
        """获取律师认证建议"""
        return {
            'required_documents': [
                '律师执业证书',
                '身份证明',
                '律师事务所执业许可证',
                '最近一年的执业记录'
            ],
            'verification_process': [
                '提交基本信息',
                '上传相关证件',
                '在线验证律师证',
                '人工审核确认',
                '认证完成'
            ],
            'api_recommendations': [
                {
                    'name': '全国律师协会查询系统',
                    'url': 'https://www.acla.org.cn/lawyer/search',
                    'description': '官方律师信息查询平台'
                },
                {
                    'name': '各地律师协会查询',
                    'url': 'https://www.localbar.org/search',
                    'description': '地方律师协会查询系统'
                },
                {
                    'name': '司法部律师查询',
                    'url': 'https://www.moj.gov.cn/lawyer',
                    'description': '司法部官方律师查询'
                }
            ],
            'verification_tips': [
                '律师证号可通过官方网站查询验证',
                '律师事务所信息可通过工商系统核实',
                '执业年限可通过律师协会记录确认',
                '专业资质可通过案例和证书验证',
                '建议定期更新律师信息和资质'
            ]
        }
    
    def create_verification_record(self, lawyer_data: Dict[str, Any], verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """创建验证记录"""
        return {
            'lawyer_info': lawyer_data,
            'verification_result': verification_result,
            'verification_time': datetime.now(),
            'status': 'completed' if verification_result['verified'] else 'failed',
            'next_steps': self._get_next_steps(verification_result)
        }
    
    def _get_next_steps(self, verification_result: Dict[str, Any]) -> list:
        """获取下一步操作建议"""
        if verification_result['verified']:
            return [
                '认证成功，可以开始接收案件',
                '建议完善个人资料和专业信息',
                '定期更新执业信息'
            ]
        else:
            return [
                '请检查律师证号是否正确',
                '确认律师姓名与证件一致',
                '联系客服获取人工审核',
                '准备相关证明材料'
            ] 