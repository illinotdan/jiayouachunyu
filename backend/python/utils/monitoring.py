"""
系统监控工具
"""

import psutil
import os
from datetime import datetime
from flask import current_app

def get_system_metrics():
    """获取系统性能指标"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used
        memory_total = memory.total
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used = disk.used
        disk_total = disk.total
        
        # 网络IO
        network = psutil.net_io_counters()
        
        # 进程信息
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            'cpu': {
                'percent': round(cpu_percent, 2),
                'cores': psutil.cpu_count()
            },
            'memory': {
                'percent': round(memory_percent, 2),
                'used': memory_used,
                'total': memory_total,
                'available': memory.available
            },
            'disk': {
                'percent': round(disk_percent, 2),
                'used': disk_used,
                'total': disk_total,
                'free': disk.free
            },
            'network': {
                'bytesSent': network.bytes_sent,
                'bytesReceived': network.bytes_recv,
                'packetsSent': network.packets_sent,
                'packetsReceived': network.packets_recv
            },
            'process': {
                'memoryRSS': process_memory.rss,
                'memoryVMS': process_memory.vms,
                'pid': os.getpid(),
                'threads': process.num_threads()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        current_app.logger.error(f"获取系统指标失败: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def check_database_health():
    """检查数据库健康状态"""
    try:
        from ..config.database import db
        
        # 执行简单查询测试连接
        result = db.session.execute("SELECT 1").scalar()
        
        if result == 1:
            return {'status': 'healthy', 'message': '数据库连接正常'}
        else:
            return {'status': 'unhealthy', 'message': '数据库查询异常'}
            
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'数据库连接失败: {str(e)}'}

def check_redis_health():
    """检查Redis健康状态"""
    try:
        from flask import current_app
        import redis
        
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        
        # 测试连接
        r.ping()
        
        # 获取Redis信息
        info = r.info()
        
        return {
            'status': 'healthy',
            'message': 'Redis连接正常',
            'version': info.get('redis_version'),
            'memory': info.get('used_memory_human'),
            'connections': info.get('connected_clients')
        }
        
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Redis连接失败: {str(e)}'}

def get_application_metrics():
    """获取应用程序指标"""
    try:
        from ..config.database import db
        from ..models.user import User
        from ..models.content import Discussion, Article
        from ..models.match import Match
        
        # 数据库连接池状态
        engine = db.engine
        pool = engine.pool
        
        pool_status = {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }
        
        # 应用统计
        app_stats = {
            'totalUsers': User.query.count(),
            'totalDiscussions': Discussion.query.count(),
            'totalArticles': Article.query.count(),
            'totalMatches': Match.query.count()
        }
        
        return {
            'databasePool': pool_status,
            'applicationStats': app_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        current_app.logger.error(f"获取应用指标失败: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
