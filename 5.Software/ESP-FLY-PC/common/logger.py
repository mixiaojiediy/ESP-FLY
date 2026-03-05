"""
Logger - 日志工具
提供统一的日志接口
"""

import logging
import sys
from typing import Optional

# 全局日志实例
_logger: Optional[logging.Logger] = None


def setup_logger(name: str = "ESP-FLY", level: int = logging.INFO) -> logging.Logger:
    """
    设置日志
    
    Args:
        name: 日志名称
        level: 日志级别
        
    Returns:
        logging.Logger: 日志实例
    """
    global _logger
    
    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    
    # 避免重复添加handler
    if not _logger.handlers:
        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # 格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        _logger.addHandler(console_handler)
    
    return _logger


def get_logger() -> logging.Logger:
    """
    获取日志实例
    
    Returns:
        logging.Logger: 日志实例
    """
    global _logger
    
    if _logger is None:
        _logger = setup_logger()
    
    return _logger
