"""
异步操作辅助工具
提供统一的异步事件循环管理，避免代码重复
"""

import asyncio
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class AsyncHelper:
    """异步操作辅助类"""
    
    @staticmethod
    def run_async(coro_func: Callable, *args, **kwargs) -> Any:
        """
        运行异步函数并返回结果
        
        Args:
            coro_func: 异步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            异步函数的执行结果
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro_func(*args, **kwargs))
        finally:
            loop.close()
    
    @staticmethod
    def async_to_sync(coro_func: Callable) -> Callable:
        """
        将异步函数转换为同步函数的修饰器
        
        Args:
            coro_func: 异步函数
            
        Returns:
            同步函数
        """
        @wraps(coro_func)
        def wrapper(*args, **kwargs):
            return AsyncHelper.run_async(coro_func, *args, **kwargs)
        return wrapper


def run_async(coro_func: Callable, *args, **kwargs) -> Any:
    """
    运行异步函数的快捷函数
    
    Args:
        coro_func: 异步函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        异步函数的执行结果
    """
    return AsyncHelper.run_async(coro_func, *args, **kwargs)


def async_context():
    """
    异步上下文管理器
    
    Returns:
        异步上下文对象
    """
    return asyncio.new_event_loop()