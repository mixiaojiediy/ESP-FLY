"""
ResourcePath - 资源路径工具
用于在打包后正确获取资源文件路径
"""
import os
import sys


def resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径
    
    在开发环境中，返回相对于项目根目录的路径
    在打包后的exe中，返回相对于临时解压目录的路径
    
    Args:
        relative_path: 相对于项目根目录的资源路径，如 "resources/models/model.obj"
        
    Returns:
        str: 资源文件的绝对路径
    """
    try:
        # PyInstaller 打包后会创建一个临时文件夹，路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境中，获取项目根目录（common 目录的父目录）
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)


def get_base_path() -> str:
    """
    获取应用程序基础路径
    
    Returns:
        str: 基础路径（开发环境为项目根目录，打包后为临时目录）
    """
    try:
        return sys._MEIPASS
    except AttributeError:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_path() -> str:
    """
    获取配置文件路径（用户可编辑的配置文件）
    
    打包后，配置文件在exe同目录的data文件夹下
    开发环境中，配置文件在项目根目录的data文件夹下
    
    Returns:
        str: 配置文件路径（exe同目录/data/config.ini 或 项目根目录/data/config.ini）
    """
    if getattr(sys, 'frozen', False):
        # 打包后的exe环境：exe同目录下的data文件夹
        exe_dir = os.path.dirname(sys.executable)
        config_dir = os.path.join(exe_dir, "data")
        # 确保data文件夹存在
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.ini")
    else:
        # 开发环境：项目根目录的data文件夹
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(base_path, "data")
        # 确保data文件夹存在
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.ini")


def get_default_config_path() -> str:
    """
    获取默认配置文件路径（打包在exe内部的资源文件）
    
    打包后，从打包资源中读取
    开发环境中，从项目根目录读取
    
    Returns:
        str: 默认配置文件路径
    """
    return resource_path("config.ini")
