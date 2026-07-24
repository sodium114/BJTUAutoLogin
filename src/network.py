import requests
import urllib3
import subprocess
import platform
import sys

# 禁用 SSL 警告（校园网环境经常有自签名证书）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Windows 隐藏 cmd 黑窗
if sys.platform == "win32":
    import ctypes
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

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

def get_wifi_ssid():
    """获取当前连接的WiFi SSID名称，未连接返回空字符串"""
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            errors='replace',
            timeout=10,
            creationflags=CREATE_NO_WINDOW
        )
        for line in result.stdout.splitlines():
            if line.strip().startswith("SSID") and ":" in line:
                ssid = line.split(":", 1)[1].strip()
                return ssid if ssid else ""
        return ""
    except:
        return ""

def _is_wifi_connected_windows():
    """Windows系统检测WiFi连接 - 检测到SSID即为已连接"""
    return bool(get_wifi_ssid())

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


