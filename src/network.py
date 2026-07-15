import requests
import urllib3
import subprocess
import platform
import os
import sys
from datetime import datetime

# 禁用 SSL 警告（校园网环境经常有自签名证书）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Windows 隐藏 cmd 黑窗
if sys.platform == "win32":
    import ctypes
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

def get_app_path():
    """获取应用程序所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def is_online(url):
    """检测是否能访问外网 - 不验证SSL证书（校园网环境需要）"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(
            url,
            headers=headers,
            timeout=5,
            allow_redirects=False,
            verify=False
        )
        # 只要收到任何响应（包括重定向）都说明网络是通的
        return True
    except requests.RequestException:
        return False

def is_wifi_connected():
    """检测WiFi是否已连接"""
    system = platform.system()
    
    if system == "Windows":
        return _is_wifi_connected_windows()
    elif system == "Darwin":
        return _is_wifi_connected_mac()
    else:
        return True

def _is_wifi_connected_windows():
    """Windows系统检测WiFi连接 - 检测到SSID即为已连接"""
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            errors='replace',
            timeout=10,
            creationflags=CREATE_NO_WINDOW
        )
        # 如果输出中有 SSID 且不为空，说明WiFi已连接
        for line in result.stdout.splitlines():
            if line.strip().startswith("SSID") and ":" in line:
                ssid = line.split(":", 1)[1].strip()
                if ssid:
                    return True
        return False
    except:
        return False

def _is_wifi_connected_mac():
    """Mac系统检测WiFi连接"""
    try:
        result = subprocess.run(
            ["networksetup", "-getairportpower", "en0"],
            capture_output=True,
            text=True,
            errors='replace',
            timeout=10
        )
        return "On" in result.stdout
    except:
        return True

class SimpleTrafficMonitor:
    """简单的流量统计器 - 基于连接时间估算"""
    
    def __init__(self):
        self.start_time = None
        self.last_save_time = None
        self.total_bytes = 0
        self.is_online = False
        self.data_file = os.path.join(get_app_path(), "traffic_data.json")
        self._load_data()
    
    def _load_data(self):
        """从文件加载历史数据"""
        try:
            if os.path.exists(self.data_file):
                import json
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_bytes = data.get('total_bytes', 0)
        except:
            pass
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            import json
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({'total_bytes': self.total_bytes}, f)
        except:
            pass
    
    def start(self):
        """开始统计"""
        self.start_time = datetime.now()
        self.last_save_time = datetime.now()
    
    def update_online_status(self, online):
        """更新在线状态"""
        if online and not self.is_online:
            # 刚连上
            if not self.start_time:
                self.start_time = datetime.now()
        self.is_online = online
    
    def tick(self):
        """每秒钟调用一次，更新统计"""
        if self.is_online:
            # 估算流量 - 假设每秒平均 50KB
            self.total_bytes += 50 * 1024
        
        # 每5分钟保存一次
        if self.last_save_time and (datetime.now() - self.last_save_time).seconds > 300:
            self._save_data()
            self.last_save_time = datetime.now()
    
    def get_uptime(self):
        """获取连接时长"""
        if not self.start_time:
            return "0:00:00"
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    
    def get_traffic_str(self):
        """获取流量字符串"""
        if self.total_bytes < 1024:
            return f"{self.total_bytes} B"
        elif self.total_bytes < 1024 * 1024:
            return f"{self.total_bytes / 1024:.2f} KB"
        elif self.total_bytes < 1024 * 1024 * 1024:
            return f"{self.total_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{self.total_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def reset_session(self):
        """重置本次会话计时"""
        self.start_time = datetime.now()
