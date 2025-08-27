"""
演示账户分析API端点
收集和分析演示账户使用数据
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, func
from datetime import datetime, timedelta
import structlog
import json

from app.core.deps import get_db

logger = structlog.get_logger()

router = APIRouter()


@router.post("/demo-conversion")
async def track_demo_conversion_events(
    analytics_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    跟踪演示账户转化事件
    
    Args:
        analytics_data: 分析数据
        request: 请求对象
        db: 数据库会话
    
    Returns:
        处理结果
    """
    try:
        session_id = analytics_data.get('session_id')
        events = analytics_data.get('events', [])
        
        if not session_id or not events:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少必要的分析数据"
            )
        
        # 这里可以将事件数据存储到数据库或发送到分析系统
        # 为了简化，我们先记录到日志
        for event in events:
            logger.info(
                "演示转化事件",
                session_id=session_id,
                event=event.get('event'),
                timestamp=event.get('timestamp'),
                page=event.get('page'),
                data=event
            )
        
        # 统计转化数据
        conversion_stats = analyze_conversion_events(events)
        
        return {
            'success': True,
            'message': f'成功记录 {len(events)} 个事件',
            'data': {
                'session_id': session_id,
                'events_processed': len(events),
                'conversion_stats': conversion_stats
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("记录演示转化事件失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="记录分析数据失败"
        )


@router.get("/demo-stats")
async def get_demo_statistics(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取演示账户统计数据
    
    Args:
        days: 统计天数
        db: 数据库会话
    
    Returns:
        统计数据
    """
    try:
        # 这里应该从数据库查询真实的统计数据
        # 为了演示，返回模拟数据
        mock_stats = {
            'total_demo_sessions': 156,
            'lawyer_demo_sessions': 89,
            'user_demo_sessions': 67,
            'conversion_rate': 0.23,
            'average_session_duration': 180, # 秒
            'top_demo_actions': [
                {'action': 'view_cases', 'count': 234},
                {'action': 'view_profile', 'count': 189},
                {'action': 'view_earnings', 'count': 145},
                {'action': 'view_statistics', 'count': 123}
            ],
            'conversion_funnel': {
                'demo_access': 156,
                'demo_engagement': 134,
                'conversion_intent': 45,
                'registration_start': 36,
                'registration_complete': 28
            },
            'daily_stats': generate_daily_demo_stats(days)
        }
        
        return {
            'success': True,
            'data': mock_stats,
            'period': f'最近 {days} 天'
        }
        
    except Exception as e:
        logger.error("获取演示统计数据失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计数据失败"
        )


@router.get("/demo-conversion-funnel")
async def get_demo_conversion_funnel(
    demo_type: str = None,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取演示账户转化漏斗数据
    
    Args:
        demo_type: 演示类型 ('lawyer' 或 'user')
        days: 统计天数
        db: 数据库会话
    
    Returns:
        转化漏斗数据
    """
    try:
        # 模拟转化漏斗数据
        if demo_type == 'lawyer':
            funnel_data = {
                'demo_type': 'lawyer',
                'funnel_steps': [
                    {'step': '访问演示页面', 'count': 89, 'rate': 1.0},
                    {'step': '进入律师演示', 'count': 76, 'rate': 0.85},
                    {'step': '查看案件列表', 'count': 68, 'rate': 0.76},
                    {'step': '查看收入统计', 'count': 54, 'rate': 0.61},
                    {'step': '点击注册按钮', 'count': 23, 'rate': 0.26},
                    {'step': '完成注册', 'count': 18, 'rate': 0.20}
                ]
            }
        elif demo_type == 'user':
            funnel_data = {
                'demo_type': 'user',
                'funnel_steps': [
                    {'step': '访问演示页面', 'count': 67, 'rate': 1.0},
                    {'step': '进入用户演示', 'count': 58, 'rate': 0.87},
                    {'step': '查看发布需求', 'count': 51, 'rate': 0.76},
                    {'step': '查看律师匹配', 'count': 43, 'rate': 0.64},
                    {'step': '点击注册按钮', 'count': 22, 'rate': 0.33},
                    {'step': '完成注册', 'count': 16, 'rate': 0.24}
                ]
            }
        else:
            # 总体数据
            funnel_data = {
                'demo_type': 'all',
                'funnel_steps': [
                    {'step': '访问演示页面', 'count': 156, 'rate': 1.0},
                    {'step': '选择演示类型', 'count': 134, 'rate': 0.86},
                    {'step': '体验演示功能', 'count': 119, 'rate': 0.76},
                    {'step': '产生转化意向', 'count': 45, 'rate': 0.29},
                    {'step': '开始注册流程', 'count': 36, 'rate': 0.23},
                    {'step': '完成注册', 'count': 28, 'rate': 0.18}
                ]
            }
        
        return {
            'success': True,
            'data': funnel_data,
            'period': f'最近 {days} 天',
            'summary': {
                'total_visitors': funnel_data['funnel_steps'][0]['count'],
                'conversion_rate': funnel_data['funnel_steps'][-1]['rate'],
                'drop_off_points': identify_drop_off_points(funnel_data['funnel_steps'])
            }
        }
        
    except Exception as e:
        logger.error("获取转化漏斗数据失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取漏斗数据失败"
        )


def analyze_conversion_events(events: List[Dict]) -> Dict[str, Any]:
    """分析转化事件"""
    stats = {
        'total_events': len(events),
        'event_types': {},
        'session_duration': 0,
        'conversion_indicators': {
            'demo_access': False,
            'demo_engagement': False,
            'conversion_intent': False,
            'registration_start': False
        }
    }
    
    # 统计事件类型
    for event in events:
        event_type = event.get('event', 'unknown')
        stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
        
        # 检查转化指标
        if event_type == 'demo_access':
            stats['conversion_indicators']['demo_access'] = True
        elif event_type == 'demo_action':
            stats['conversion_indicators']['demo_engagement'] = True
        elif event_type == 'demo_conversion_intent':
            stats['conversion_indicators']['conversion_intent'] = True
        elif event_type == 'demo_to_registration':
            stats['conversion_indicators']['registration_start'] = True
    
    # 计算会话时长
    if events:
        timestamps = [e.get('timestamp', 0) for e in events if e.get('timestamp')]
        if len(timestamps) > 1:
            stats['session_duration'] = (max(timestamps) - min(timestamps)) / 1000  # 转换为秒
    
    return stats


def generate_daily_demo_stats(days: int) -> List[Dict]:
    """生成每日演示统计数据"""
    daily_stats = []
    base_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        # 模拟数据，实际应该从数据库查询
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'demo_sessions': max(0, 20 + (i % 7) * 3 - 5),
            'conversions': max(0, 4 + (i % 5) - 2),
            'conversion_rate': round(0.15 + (i % 10) * 0.02, 3)
        })
    
    return daily_stats


def identify_drop_off_points(funnel_steps: List[Dict]) -> List[Dict]:
    """识别转化漏斗的流失点"""
    drop_offs = []
    
    for i in range(len(funnel_steps) - 1):
        current_step = funnel_steps[i]
        next_step = funnel_steps[i + 1]
        
        drop_off_rate = 1 - (next_step['rate'] / current_step['rate'])
        
        if drop_off_rate > 0.3:  # 流失率超过30%
            drop_offs.append({
                'from_step': current_step['step'],
                'to_step': next_step['step'],
                'drop_off_rate': round(drop_off_rate, 3),
                'lost_users': current_step['count'] - next_step['count']
            })
    
    return drop_offs