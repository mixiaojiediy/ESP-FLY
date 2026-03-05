"""
ConfigService - 配置服务
负责读取和保存应用程序配置
"""

import os
import sys
import shutil
import configparser
from typing import Any, Optional
from common.resource_path import get_config_path, get_default_config_path


class ConfigService:
    """
    配置服务
    
    职责：
    - 读取config.ini配置文件
    - 提供配置项的类型安全访问
    - 保存配置修改
    """
    
    DEFAULT_CONFIG_FILE = "config.ini"
    
    def __init__(self, config_file: str = None):
        """
        初始化配置服务
        
        Args:
            config_file: 配置文件路径，默认为项目根目录下的config.ini
        """
        if config_file:
            self._config_file = config_file
        else:
            # 使用资源路径工具获取配置文件路径（支持打包后的exe）
            self._config_file = get_config_path()
        
        self._config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 优先使用用户配置文件（exe同目录）
        if os.path.exists(self._config_file):
            try:
                self._config.read(self._config_file, encoding='utf-8')
                return
            except Exception as e:
                print(f"[ConfigService] 加载配置文件失败: {e}")
        
        # 如果用户配置文件不存在，尝试从打包资源中读取默认配置
        default_config_path = get_default_config_path()
        if os.path.exists(default_config_path):
            try:
                self._config.read(default_config_path, encoding='utf-8')
                print(f"[ConfigService] 使用默认配置文件: {default_config_path}")
                # 将默认配置复制到用户配置位置，方便后续修改
                try:
                    shutil.copy2(default_config_path, self._config_file)
                    print(f"[ConfigService] 已复制默认配置到: {self._config_file}")
                except Exception as e:
                    print(f"[ConfigService] 复制默认配置失败（可忽略）: {e}")
            except Exception as e:
                print(f"[ConfigService] 加载默认配置文件失败: {e}")
        else:
            print(f"[ConfigService] 未找到配置文件，使用默认配置值")
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                self._config.write(f)
            return True
        except Exception as e:
            print(f"[ConfigService] 保存配置文件失败: {e}")
            return False
    
    # ========== 类型安全的配置读取 ==========
    
    def get_string(self, section: str, key: str, default: str = "") -> str:
        """获取字符串配置"""
        try:
            return self._config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """获取整数配置"""
        try:
            return self._config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def get_float(self, section: str, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        try:
            return self._config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        try:
            return self._config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    # ========== 配置写入 ==========
    
    def set_value(self, section: str, key: str, value: Any):
        """设置配置值"""
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, str(value))
    
    # ========== 便捷方法 ==========
    
    def get_network_config(self) -> dict:
        """获取网络配置"""
        return {
            'drone_ip': self.get_string('Network', 'drone_ip', '192.168.43.42'),
            'port': self.get_int('Network', 'port', 2390),
        }
    
    def get_control_config(self) -> dict:
        """获取控制配置"""
        return {
            'max_angle': self.get_float('Control', 'max_angle', 30.0),
            'max_yaw': self.get_float('Control', 'max_yaw', 180.0),
            'max_thrust': self.get_int('Control', 'max_thrust', 65535),
            'angle_step': self.get_float('Control', 'angle_step', 1.0),
            'thrust_step': self.get_int('Control', 'thrust_step', 1000),
        }
    
    def get_ui_config(self) -> dict:
        """获取UI配置"""
        return {
            'window_width': self.get_int('UI', 'window_width', 1280),
            'window_height': self.get_int('UI', 'window_height', 800),
            'refresh_rate': self.get_int('UI', 'view_3d_refresh_rate', 50),
        }
    
    def get_debug_config(self) -> dict:
        """获取调试配置"""
        return {
            'print_rx_raw_packets': self.get_bool('Debug', 'print_rx_raw_packets', False),
            'print_rx_drone_status': self.get_bool('Debug', 'print_rx_drone_status', False),
        }
    
    def get_pid_config(self) -> dict:
        """获取PID配置"""
        return {
            # PID参数范围
            'pid_p_min': self.get_float('PID', 'pid_p_min', 0.0),
            'pid_p_max': self.get_float('PID', 'pid_p_max', 1000.0),
            'pid_i_min': self.get_float('PID', 'pid_i_min', 0.0),
            'pid_i_max': self.get_float('PID', 'pid_i_max', 1000.0),
            'pid_d_min': self.get_float('PID', 'pid_d_min', 0.0),
            'pid_d_max': self.get_float('PID', 'pid_d_max', 1000.0),
            # 角速度环（内环）
            'rate_roll_p': self.get_float('PID', 'rate_roll_p', 3.5),
            'rate_roll_i': self.get_float('PID', 'rate_roll_i', 0.0),
            'rate_roll_d': self.get_float('PID', 'rate_roll_d', 0.0),
            'rate_pitch_p': self.get_float('PID', 'rate_pitch_p', 3.5),
            'rate_pitch_i': self.get_float('PID', 'rate_pitch_i', 0.0),
            'rate_pitch_d': self.get_float('PID', 'rate_pitch_d', 0.0),
            'rate_yaw_p': self.get_float('PID', 'rate_yaw_p', 2.5),
            'rate_yaw_i': self.get_float('PID', 'rate_yaw_i', 0.0),
            'rate_yaw_d': self.get_float('PID', 'rate_yaw_d', 0.0),
            # 角度环（外环）
            'angle_roll_p': self.get_float('PID', 'angle_roll_p', 6.0),
            'angle_roll_i': self.get_float('PID', 'angle_roll_i', 0.0),
            'angle_roll_d': self.get_float('PID', 'angle_roll_d', 0.0),
            'angle_pitch_p': self.get_float('PID', 'angle_pitch_p', 6.0),
            'angle_pitch_i': self.get_float('PID', 'angle_pitch_i', 0.0),
            'angle_pitch_d': self.get_float('PID', 'angle_pitch_d', 0.0),
            'angle_yaw_p': self.get_float('PID', 'angle_yaw_p', 6.0),
            'angle_yaw_i': self.get_float('PID', 'angle_yaw_i', 0.0),
            'angle_yaw_d': self.get_float('PID', 'angle_yaw_d', 0.0),
        }
    
    def save_pid_config(self, pid_config: dict) -> bool:
        """保存PID配置"""
        try:
            # 确保PID部分存在
            if not self._config.has_section('PID'):
                self._config.add_section('PID')
            
            # 保存PID参数范围
            if 'pid_p_min' in pid_config:
                self.set_value('PID', 'pid_p_min', pid_config['pid_p_min'])
            if 'pid_p_max' in pid_config:
                self.set_value('PID', 'pid_p_max', pid_config['pid_p_max'])
            if 'pid_i_min' in pid_config:
                self.set_value('PID', 'pid_i_min', pid_config['pid_i_min'])
            if 'pid_i_max' in pid_config:
                self.set_value('PID', 'pid_i_max', pid_config['pid_i_max'])
            if 'pid_d_min' in pid_config:
                self.set_value('PID', 'pid_d_min', pid_config['pid_d_min'])
            if 'pid_d_max' in pid_config:
                self.set_value('PID', 'pid_d_max', pid_config['pid_d_max'])
            
            # 保存角速度环（内环）参数
            if 'rate_roll_p' in pid_config:
                self.set_value('PID', 'rate_roll_p', pid_config['rate_roll_p'])
            if 'rate_roll_i' in pid_config:
                self.set_value('PID', 'rate_roll_i', pid_config['rate_roll_i'])
            if 'rate_roll_d' in pid_config:
                self.set_value('PID', 'rate_roll_d', pid_config['rate_roll_d'])
            if 'rate_pitch_p' in pid_config:
                self.set_value('PID', 'rate_pitch_p', pid_config['rate_pitch_p'])
            if 'rate_pitch_i' in pid_config:
                self.set_value('PID', 'rate_pitch_i', pid_config['rate_pitch_i'])
            if 'rate_pitch_d' in pid_config:
                self.set_value('PID', 'rate_pitch_d', pid_config['rate_pitch_d'])
            if 'rate_yaw_p' in pid_config:
                self.set_value('PID', 'rate_yaw_p', pid_config['rate_yaw_p'])
            if 'rate_yaw_i' in pid_config:
                self.set_value('PID', 'rate_yaw_i', pid_config['rate_yaw_i'])
            if 'rate_yaw_d' in pid_config:
                self.set_value('PID', 'rate_yaw_d', pid_config['rate_yaw_d'])
            
            # 保存角度环（外环）参数
            if 'angle_roll_p' in pid_config:
                self.set_value('PID', 'angle_roll_p', pid_config['angle_roll_p'])
            if 'angle_roll_i' in pid_config:
                self.set_value('PID', 'angle_roll_i', pid_config['angle_roll_i'])
            if 'angle_roll_d' in pid_config:
                self.set_value('PID', 'angle_roll_d', pid_config['angle_roll_d'])
            if 'angle_pitch_p' in pid_config:
                self.set_value('PID', 'angle_pitch_p', pid_config['angle_pitch_p'])
            if 'angle_pitch_i' in pid_config:
                self.set_value('PID', 'angle_pitch_i', pid_config['angle_pitch_i'])
            if 'angle_pitch_d' in pid_config:
                self.set_value('PID', 'angle_pitch_d', pid_config['angle_pitch_d'])
            if 'angle_yaw_p' in pid_config:
                self.set_value('PID', 'angle_yaw_p', pid_config['angle_yaw_p'])
            if 'angle_yaw_i' in pid_config:
                self.set_value('PID', 'angle_yaw_i', pid_config['angle_yaw_i'])
            if 'angle_yaw_d' in pid_config:
                self.set_value('PID', 'angle_yaw_d', pid_config['angle_yaw_d'])
            
            return self.save_config()
        except Exception as e:
            print(f"[ConfigService] 保存PID配置失败: {e}")
            return False
