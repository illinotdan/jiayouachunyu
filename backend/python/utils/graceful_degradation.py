"""
优雅降级机制
当外部依赖不可用时，提供降级服务而不是完全失败
"""

import logging
import time
import threading
from typing import Any, Callable, Dict, Optional, Union, List
from functools import wraps
from contextlib import contextmanager
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服务状态枚举"""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

@dataclass
class CircuitBreakerState:
    """断路器状态"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    status: ServiceStatus = ServiceStatus.AVAILABLE
    last_success_time: Optional[datetime] = None

class CircuitBreaker:
    """断路器模式实现"""

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.state = CircuitBreakerState()
        self._lock = threading.Lock()

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置断路器"""
        if self.state.status != ServiceStatus.UNAVAILABLE:
            return False

        if not self.state.last_failure_time:
            return True

        return datetime.now() - self.state.last_failure_time > timedelta(seconds=self.recovery_timeout)

    def _on_success(self):
        """成功时的处理"""
        with self._lock:
            self.state.failure_count = 0
            self.state.status = ServiceStatus.AVAILABLE
            self.state.last_success_time = datetime.now()

    def _on_failure(self):
        """失败时的处理"""
        with self._lock:
            self.state.failure_count += 1
            self.state.last_failure_time = datetime.now()

            if self.state.failure_count >= self.failure_threshold:
                self.state.status = ServiceStatus.UNAVAILABLE
                logger.warning(f"Circuit breaker opened due to {self.state.failure_count} failures")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数调用，应用断路器逻辑"""
        if self.state.status == ServiceStatus.UNAVAILABLE and not self._should_attempt_reset():
            raise CircuitBreakerOpenException("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def __call__(self, func: Callable) -> Callable:
        """装饰器形式使用"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper

class CircuitBreakerOpenException(Exception):
    """断路器开启异常"""
    pass

class ServiceRegistry:
    """服务注册表 - 管理所有可降级的服务"""

    def __init__(self):
        self.services: Dict[str, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def register_service(self,
                        name: str,
                        primary_func: Callable,
                        fallback_func: Optional[Callable] = None,
                        circuit_breaker_config: Optional[Dict] = None):
        """注册服务"""
        with self._lock:
            # 创建断路器
            cb_config = circuit_breaker_config or {}
            circuit_breaker = CircuitBreaker(**cb_config)

            self.services[name] = {
                'primary_func': primary_func,
                'fallback_func': fallback_func,
                'circuit_breaker': circuit_breaker,
                'status': ServiceStatus.AVAILABLE
            }
            self.circuit_breakers[name] = circuit_breaker

        logger.info(f"Registered service: {name}")

    def call_service(self, name: str, *args, **kwargs) -> Any:
        """调用服务（带降级机制）"""
        if name not in self.services:
            raise ValueError(f"Service {name} not registered")

        service = self.services[name]
        circuit_breaker = service['circuit_breaker']
        primary_func = service['primary_func']
        fallback_func = service['fallback_func']

        try:
            # 尝试调用主服务
            result = circuit_breaker.call(primary_func, *args, **kwargs)
            return result
        except (CircuitBreakerOpenException, Exception) as e:
            logger.warning(f"Primary service {name} failed: {e}")

            # 尝试降级服务
            if fallback_func:
                try:
                    logger.info(f"Using fallback for service: {name}")
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback for {name} also failed: {fallback_error}")
                    raise fallback_error
            else:
                logger.error(f"No fallback available for service: {name}")
                raise e

    def get_service_status(self, name: str) -> Dict[str, Any]:
        """获取服务状态"""
        if name not in self.services:
            return {'status': 'not_registered'}

        circuit_breaker = self.circuit_breakers[name]
        return {
            'status': circuit_breaker.state.status.value,
            'failure_count': circuit_breaker.state.failure_count,
            'last_failure_time': circuit_breaker.state.last_failure_time.isoformat() if circuit_breaker.state.last_failure_time else None,
            'last_success_time': circuit_breaker.state.last_success_time.isoformat() if circuit_breaker.state.last_success_time else None
        }

    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务状态"""
        return {name: self.get_service_status(name) for name in self.services.keys()}

# 全局服务注册表
service_registry = ServiceRegistry()

def with_fallback(fallback_func: Optional[Callable] = None,
                 circuit_breaker_config: Optional[Dict] = None):
    """降级装饰器"""
    def decorator(primary_func: Callable) -> Callable:
        service_name = f"{primary_func.__module__}.{primary_func.__name__}"

        # 注册服务
        service_registry.register_service(
            name=service_name,
            primary_func=primary_func,
            fallback_func=fallback_func,
            circuit_breaker_config=circuit_breaker_config
        )

        @wraps(primary_func)
        def wrapper(*args, **kwargs):
            return service_registry.call_service(service_name, *args, **kwargs)

        return wrapper
    return decorator

class DatabaseFallback:
    """数据库降级机制"""

    def __init__(self):
        self._cache = {}
        self._cache_ttl = {}
        self.default_ttl = 300  # 5分钟

    def cache_result(self, key: str, result: Any, ttl: Optional[int] = None):
        """缓存结果"""
        expire_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
        self._cache[key] = result
        self._cache_ttl[key] = expire_time

    def get_cached_result(self, key: str) -> Optional[Any]:
        """获取缓存结果"""
        if key not in self._cache:
            return None

        if datetime.now() > self._cache_ttl[key]:
            # 缓存过期
            del self._cache[key]
            del self._cache_ttl[key]
            return None

        return self._cache[key]

    def create_fallback_query(self, cache_key: str, ttl: Optional[int] = None):
        """创建数据库查询的降级函数"""
        def fallback(*args, **kwargs):
            cached_result = self.get_cached_result(cache_key)
            if cached_result is not None:
                logger.info(f"Returning cached result for {cache_key}")
                return cached_result
            else:
                logger.warning(f"No cached data available for {cache_key}")
                return []  # 返回空结果而不是失败

        return fallback

class RedisFallback:
    """Redis降级机制"""

    def __init__(self):
        self._memory_cache = {}
        self._memory_cache_ttl = {}

    def set_memory_cache(self, key: str, value: Any, ttl: int = 300):
        """设置内存缓存"""
        expire_time = datetime.now() + timedelta(seconds=ttl)
        self._memory_cache[key] = value
        self._memory_cache_ttl[key] = expire_time

    def get_memory_cache(self, key: str) -> Optional[Any]:
        """获取内存缓存"""
        if key not in self._memory_cache:
            return None

        if datetime.now() > self._memory_cache_ttl[key]:
            del self._memory_cache[key]
            del self._memory_cache_ttl[key]
            return None

        return self._memory_cache[key]

    def create_redis_fallback(self):
        """创建Redis的降级机制"""
        def fallback_set(key: str, value: Any, ttl: int = 300):
            self.set_memory_cache(key, value, ttl)
            return True

        def fallback_get(key: str):
            return self.get_memory_cache(key)

        def fallback_delete(key: str):
            if key in self._memory_cache:
                del self._memory_cache[key]
                del self._memory_cache_ttl[key]
            return True

        return {
            'set': fallback_set,
            'get': fallback_get,
            'delete': fallback_delete
        }

class APIFallback:
    """外部API降级机制"""

    def __init__(self):
        self.static_responses = {}
        self.cached_responses = {}

    def register_static_response(self, api_name: str, response: Any):
        """注册静态响应"""
        self.static_responses[api_name] = response

    def create_api_fallback(self, api_name: str, static_response: Optional[Any] = None):
        """创建API降级函数"""
        if static_response:
            self.register_static_response(api_name, static_response)

        def fallback(*args, **kwargs):
            # 首先尝试返回缓存的响应
            if api_name in self.cached_responses:
                logger.info(f"Returning cached response for {api_name}")
                return self.cached_responses[api_name]

            # 然后尝试返回静态响应
            if api_name in self.static_responses:
                logger.info(f"Returning static response for {api_name}")
                return self.static_responses[api_name]

            # 最后返回空响应
            logger.warning(f"No fallback data available for {api_name}")
            return {'data': [], 'status': 'degraded', 'message': f'{api_name} service unavailable'}

        return fallback

# 全局降级实例
db_fallback = DatabaseFallback()
redis_fallback = RedisFallback()
api_fallback = APIFallback()

def setup_graceful_degradation():
    """设置优雅降级机制"""

    # 设置一些静态响应作为最后的降级选项
    api_fallback.register_static_response('opendota_heroes', {
        'data': [
            {'id': 1, 'name': 'Anti-Mage', 'primary_attr': 'agi'},
            {'id': 2, 'name': 'Axe', 'primary_attr': 'str'},
            # 基础英雄数据
        ],
        'status': 'static',
        'message': 'Using static hero data'
    })

    api_fallback.register_static_response('opendota_matches', {
        'data': [],
        'status': 'degraded',
        'message': 'Match data temporarily unavailable'
    })

    logger.info("Graceful degradation mechanisms initialized")

@contextmanager
def service_timeout(timeout_seconds: int = 30):
    """服务超时上下文管理器"""
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")

    # 设置超时信号
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def resilient_service_call(func: Callable,
                          fallback: Optional[Callable] = None,
                          retries: int = 3,
                          backoff_factor: float = 1.0,
                          timeout: int = 30):
    """弹性服务调用 - 重试 + 降级 + 超时"""

    for attempt in range(retries):
        try:
            with service_timeout(timeout):
                return func()
        except Exception as e:
            if attempt == retries - 1:  # 最后一次尝试
                if fallback:
                    logger.warning(f"All retries failed, using fallback: {e}")
                    return fallback()
                else:
                    raise e
            else:
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)

class ServiceMonitor:
    """服务监控 - 跟踪服务健康状态"""

    def __init__(self):
        self.metrics = {}
        self._lock = threading.Lock()

    def record_service_call(self, service_name: str, success: bool, response_time: float):
        """记录服务调用"""
        with self._lock:
            if service_name not in self.metrics:
                self.metrics[service_name] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_response_time': 0.0,
                    'last_call_time': None
                }

            metrics = self.metrics[service_name]
            metrics['total_calls'] += 1
            metrics['total_response_time'] += response_time
            metrics['last_call_time'] = datetime.now()

            if success:
                metrics['successful_calls'] += 1
            else:
                metrics['failed_calls'] += 1

    def get_service_metrics(self, service_name: str) -> Dict[str, Any]:
        """获取服务指标"""
        if service_name not in self.metrics:
            return {}

        metrics = self.metrics[service_name]
        avg_response_time = metrics['total_response_time'] / max(metrics['total_calls'], 1)
        success_rate = metrics['successful_calls'] / max(metrics['total_calls'], 1)

        return {
            'total_calls': metrics['total_calls'],
            'successful_calls': metrics['successful_calls'],
            'failed_calls': metrics['failed_calls'],
            'success_rate': success_rate,
            'average_response_time': avg_response_time,
            'last_call_time': metrics['last_call_time'].isoformat() if metrics['last_call_time'] else None
        }

# 全局服务监控实例
service_monitor = ServiceMonitor()