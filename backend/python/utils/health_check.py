"""
世界级健康检查和监控系统
提供全面的系统健康状态监控
"""

import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import asyncio
import threading

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    status: HealthStatus
    message: str
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'response_time': self.response_time,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

class HealthChecker:
    """健康检查器基类"""

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout

    def check(self) -> HealthCheckResult:
        """执行健康检查"""
        start_time = time.time()
        try:
            result = self._perform_check()
            response_time = time.time() - start_time

            return HealthCheckResult(
                name=self.name,
                status=result.get('status', HealthStatus.UNKNOWN),
                message=result.get('message', 'No message'),
                response_time=response_time,
                metadata=result.get('metadata', {})
            )
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Health check failed for {self.name}: {e}")
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                response_time=response_time
            )

    def _perform_check(self) -> Dict[str, Any]:
        """子类需要实现的检查逻辑"""
        raise NotImplementedError

class DatabaseHealthChecker(HealthChecker):
    """数据库健康检查"""

    def __init__(self, db_session_factory, timeout: float = 5.0):
        super().__init__("database", timeout)
        self.db_session_factory = db_session_factory

    def _perform_check(self) -> Dict[str, Any]:
        try:
            with self.db_session_factory() as session:
                result = session.execute("SELECT 1").fetchone()
                if result:
                    return {
                        'status': HealthStatus.HEALTHY,
                        'message': 'Database connection successful',
                        'metadata': {'connection_pool_size': session.bind.pool.size()}
                    }
                else:
                    return {
                        'status': HealthStatus.UNHEALTHY,
                        'message': 'Database query returned no result'
                    }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'Database connection failed: {str(e)}'
            }

class RedisHealthChecker(HealthChecker):
    """Redis健康检查"""

    def __init__(self, redis_client, timeout: float = 5.0):
        super().__init__("redis", timeout)
        self.redis_client = redis_client

    def _perform_check(self) -> Dict[str, Any]:
        try:
            # 执行ping命令
            response = self.redis_client.ping()
            if response:
                # 获取Redis信息
                info = self.redis_client.info()
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': 'Redis connection successful',
                    'metadata': {
                        'version': info.get('redis_version', 'unknown'),
                        'connected_clients': info.get('connected_clients', 0),
                        'used_memory_human': info.get('used_memory_human', 'unknown')
                    }
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY,
                    'message': 'Redis ping failed'
                }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'Redis connection failed: {str(e)}'
            }

class APIHealthChecker(HealthChecker):
    """外部API健康检查"""

    def __init__(self, api_name: str, health_url: str, timeout: float = 10.0):
        super().__init__(f"api_{api_name}", timeout)
        self.api_name = api_name
        self.health_url = health_url

    def _perform_check(self) -> Dict[str, Any]:
        try:
            import requests
            response = requests.get(self.health_url, timeout=self.timeout)

            if response.status_code == 200:
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': f'{self.api_name} API is healthy',
                    'metadata': {
                        'status_code': response.status_code,
                        'response_size': len(response.content)
                    }
                }
            else:
                return {
                    'status': HealthStatus.DEGRADED,
                    'message': f'{self.api_name} API returned status {response.status_code}',
                    'metadata': {'status_code': response.status_code}
                }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'{self.api_name} API check failed: {str(e)}'
            }

class SystemHealthChecker(HealthChecker):
    """系统资源健康检查"""

    def __init__(self, timeout: float = 2.0):
        super().__init__("system", timeout)

    def _perform_check(self) -> Dict[str, Any]:
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()

            # 磁盘使用情况
            disk = psutil.disk_usage('/')

            # 判断健康状态
            status = HealthStatus.HEALTHY
            messages = []

            if cpu_percent > 90:
                status = HealthStatus.DEGRADED
                messages.append(f"High CPU usage: {cpu_percent}%")

            if memory.percent > 90:
                status = HealthStatus.DEGRADED
                messages.append(f"High memory usage: {memory.percent}%")

            if disk.percent > 90:
                status = HealthStatus.DEGRADED
                messages.append(f"High disk usage: {disk.percent}%")

            message = "; ".join(messages) if messages else "System resources are healthy"

            return {
                'status': status,
                'message': message,
                'metadata': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent,
                    'disk_free': disk.free
                }
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'System check failed: {str(e)}'
            }

class HealthMonitor:
    """健康监控管理器"""

    def __init__(self):
        self.checkers: Dict[str, HealthChecker] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self.start_time = datetime.now()
        self._lock = threading.Lock()

    def register_checker(self, checker: HealthChecker):
        """注册健康检查器"""
        with self._lock:
            self.checkers[checker.name] = checker
        logger.info(f"Registered health checker: {checker.name}")

    def unregister_checker(self, name: str):
        """取消注册健康检查器"""
        with self._lock:
            if name in self.checkers:
                del self.checkers[name]
                if name in self.last_results:
                    del self.last_results[name]
        logger.info(f"Unregistered health checker: {name}")

    def check_health(self, checker_names: Optional[List[str]] = None) -> Dict[str, HealthCheckResult]:
        """执行健康检查"""
        if checker_names is None:
            checker_names = list(self.checkers.keys())

        results = {}
        with ThreadPoolExecutor(max_workers=len(checker_names)) as executor:
            future_to_name = {
                executor.submit(self.checkers[name].check): name
                for name in checker_names if name in self.checkers
            }

            for future in future_to_name:
                name = future_to_name[future]
                try:
                    result = future.result(timeout=self.checkers[name].timeout)
                    results[name] = result
                    self.last_results[name] = result
                except TimeoutError:
                    result = HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check timed out after {self.checkers[name].timeout}s",
                        response_time=self.checkers[name].timeout
                    )
                    results[name] = result
                    self.last_results[name] = result
                except Exception as e:
                    logger.error(f"Health check error for {name}: {e}")
                    result = HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {str(e)}",
                        response_time=0
                    )
                    results[name] = result
                    self.last_results[name] = result

        return results

    def get_overall_status(self) -> HealthStatus:
        """获取整体健康状态"""
        if not self.last_results:
            return HealthStatus.UNKNOWN

        statuses = [result.status for result in self.last_results.values()]

        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        current_results = self.check_health()
        overall_status = self.get_overall_status()

        uptime = datetime.now() - self.start_time

        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'checks': {name: result.to_dict() for name, result in current_results.items()},
            'summary': {
                'total_checks': len(current_results),
                'healthy_checks': len([r for r in current_results.values() if r.status == HealthStatus.HEALTHY]),
                'degraded_checks': len([r for r in current_results.values() if r.status == HealthStatus.DEGRADED]),
                'unhealthy_checks': len([r for r in current_results.values() if r.status == HealthStatus.UNHEALTHY])
            }
        }

# 全局健康监控实例
health_monitor = HealthMonitor()

def setup_default_health_checks(app, db=None, redis_client=None):
    """设置默认的健康检查"""

    # 系统资源检查
    health_monitor.register_checker(SystemHealthChecker())

    # 数据库检查
    if db is not None:
        try:
            health_monitor.register_checker(DatabaseHealthChecker(db.session))
        except Exception as e:
            logger.warning(f"Failed to register database health checker: {e}")

    # Redis检查
    if redis_client is not None:
        try:
            health_monitor.register_checker(RedisHealthChecker(redis_client))
        except Exception as e:
            logger.warning(f"Failed to register Redis health checker: {e}")

    # 外部API检查（可选）
    # health_monitor.register_checker(APIHealthChecker("opendota", "https://api.opendota.com/api/health"))

    logger.info(f"Health monitoring initialized with {len(health_monitor.checkers)} checkers")

def create_health_blueprint():
    """创建健康检查蓝图"""
    from flask import Blueprint, jsonify, request

    health_bp = Blueprint('health', __name__, url_prefix='/health')

    @health_bp.route('/', methods=['GET'])
    def health_check():
        """基础健康检查端点"""
        try:
            summary = health_monitor.get_health_summary()
            status_code = 200 if summary['status'] == 'healthy' else 503
            return jsonify(summary), status_code
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'message': f'Health check system error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }), 500

    @health_bp.route('/live', methods=['GET'])
    def liveness_probe():
        """存活性探针 - 用于Kubernetes等容器编排"""
        return jsonify({
            'status': 'alive',
            'timestamp': datetime.now().isoformat()
        }), 200

    @health_bp.route('/ready', methods=['GET'])
    def readiness_probe():
        """就绪性探针 - 检查是否准备好接受流量"""
        results = health_monitor.check_health(['database', 'redis'])

        # 如果关键服务都健康，则认为准备就绪
        critical_services_healthy = all(
            result.status == HealthStatus.HEALTHY
            for result in results.values()
        )

        if critical_services_healthy:
            return jsonify({
                'status': 'ready',
                'timestamp': datetime.now().isoformat(),
                'checks': {name: result.to_dict() for name, result in results.items()}
            }), 200
        else:
            return jsonify({
                'status': 'not_ready',
                'timestamp': datetime.now().isoformat(),
                'checks': {name: result.to_dict() for name, result in results.items()}
            }), 503

    @health_bp.route('/detailed', methods=['GET'])
    def detailed_health():
        """详细健康检查"""
        checker_names = request.args.getlist('check')
        results = health_monitor.check_health(checker_names if checker_names else None)

        return jsonify({
            'checks': {name: result.to_dict() for name, result in results.items()},
            'timestamp': datetime.now().isoformat()
        })

    return health_bp