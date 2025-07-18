import logging
import threading
from functools import wraps
from typing import Any, Callable
import time

logger = logging.getLogger(__name__)
def time_this(func: Callable[..., Any]):
    """记录函数的运行时间装饰器

    Args:
        func (Callable[..., Any]): 被修饰函数

    Returns:
        Callable[..., Any]: 返回一个装饰器函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        ret = func(*args, **kwargs)
        end = time.perf_counter()
        logger.debug(f"{func.__name__} took {end - start: .5f}s")
        return ret
    return wrapper


def synchronized(func: Callable[..., Any]):
    """线程锁装饰器

    Args:
        func (Callable[..., Any]): 被线程锁装饰的函数

    Returns:
        Callable[..., Any]: 返回一个装饰器函数
    """
    func.__lock__ = threading.Lock()
    @wraps(func)
    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)
    return lock_func

def singleton(cls):
    """单例模式装饰器
    
    增加了线程锁，保证多线程下的单例创建可靠

    Args:
        cls: 要装饰的类
        
    Returns:
        Callable[..., Any]: 返回一个装饰器函数
    """
    _instance = {}
    @synchronized
    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]
    return _singleton


def flyweight(cls):
    """享元模式装饰器

    减少相同参数的类实例的内存消耗，适用频繁创建大量相似对象场景
    
    Args:
        cls: 要装饰的类
    
    Returns:
        Callable[..., Any]: 返回一个装饰器函数
    """
    
    _instance = {}
    
    def _to_key(args, kwargs):
        key = args
        if kwargs:
            sorted_items = sorted(kwargs.items())
            key += tuple(sorted_items)
        return key
    @synchronized
    def _flyweight(*args, **kwargs):
        cache_key = f"{cls}_{_to_key(args, kwargs)}"
        if cache_key not in _instance:
            _instance[cache_key] = cls(*args, **kwargs)
        return _instance[cache_key]
    
    return _flyweight