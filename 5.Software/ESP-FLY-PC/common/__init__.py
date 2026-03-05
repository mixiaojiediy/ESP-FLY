"""
Common - 公共组件
包含日志工具、可观察对象基类等
"""

from .logger import get_logger, setup_logger
from .resource_path import resource_path, get_base_path, get_config_path, get_default_config_path

__all__ = [
    'get_logger',
    'setup_logger',
    'resource_path',
    'get_base_path',
    'get_config_path',
    'get_default_config_path',
]
