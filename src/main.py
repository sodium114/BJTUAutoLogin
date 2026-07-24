"""
BJTU 校园网自动登录 — PyWebView + HTML 版本
"""
import json
import time
import threading
import signal
import sys
import os
import webbrowser
import ctypes

# 高DPI适配
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass


def _set_window_icon(window, icon_path):
    """通过 Win32 API 设置窗口图标（开发模式和打包后均可用）"""
    try:
        import ctypes as ct
        from ctypes import wintypes

        hwnd = window._native_hwnd if hasattr(window, '_native_hwnd') else None
        if not hwnd:
            # 某些 pywebview 版本使用不同的属性名
            for attr in ('_hwnd', 'hwnd', '_handle', '_native_handle'):
                if hasattr(window, attr):
                    hwnd = getattr(window, attr)
                    break
        if not hwnd:
            return

        # 加载图标
        icon_handle = ct.windll.user32.LoadImageW(
            0, icon_path, 1,  # IMAGE_ICON
            0, 0, 0x00000010 | 0x00000040  # LR_LOADFROMFILE | LR_DEFAULTSIZE
        )
        if icon_handle:
            # 设置窗口图标（大图标 + 小图标）
            ct.windll.user32.SendMessageW(hwnd, 0x0080, 1, icon_handle)  # WM_SETICON ICON_BIG
            ct.windll.user32.SendMessageW(hwnd, 0x0080, 0, icon_handle)  # WM_SETICON ICON_SMALL
    except Exception:
        pass  # 图标设置失败不影响主功能


def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_config_path():
    app_path = get_app_path()
    for p in [os.path.join(app_path, "config.json"),
              os.path.join(app_path, "resources", "config.json")]:
        if os.path.exists(p):
            return p
    return os.path.join(app_path, "config.json")


try:
    from logger import logger, get_app_path
    from network import is_online, is_wifi_connected, get_wifi_ssid
    from portal import Portal
except Exception as e:
    print(f"导入模块错误: {e}")
    import traceback
    traceback.print_exc()
    time.sleep(5)
    sys.exit(1)


# ========== PyWebView JS API ==========

class Api:
    """暴露给前端 JavaScript 的 Python API"""

    def __init__(self, app):
        self._app = app

    def login(self, username="", password=""):
        if username and password:
            self._app.cfg["username"] = username
            self._app.cfg["password"] = password
            self._app.portal = Portal(username, password)
        logger.log("手动触发登录...")
        success, message = self._app.portal.login()
        tag = "成功" if success else "失败"
        logger.log(f"登录{tag}：{message}")
        return {"success": success, "message": message}

    def save_config(self, username, password):
        self._app.cfg["username"] = username
        self._app.cfg["password"] = password
        self._app.portal = Portal(username, password)
        try:
            config_path = get_config_path()
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._app.cfg, f, indent=2, ensure_ascii=False)
            logger.log("配置已保存")
            return True
        except Exception as e:
            logger.log(f"保存配置失败: {e}")
            return False

    def load_config(self):
        return {
            "username": self._app.cfg.get("username", ""),
            "password": self._app.cfg.get("password", ""),
            "check_interval": self._app.cfg.get("check_interval", 60),
            "retry_interval": self._app.cfg.get("retry_interval", 10),
        }

    def get_status(self):
        return {
            "wifi_connected": self._app.wifi_connected,
            "wifi_ssid": self._app.wifi_ssid,
            "net_connected": self._app.net_connected,
        }

    def refresh_status(self):
        """强制重新检测网络状态"""
        logger.log("手动刷新网络状态...")
        self._app.wifi_connected = is_wifi_connected()
        self._app.wifi_ssid = get_wifi_ssid() if self._app.wifi_connected else ""
        self._app.net_connected = is_online(self._app.test_url)
        return {
            "wifi_connected": self._app.wifi_connected,
            "wifi_ssid": self._app.wifi_ssid,
            "net_connected": self._app.net_connected,
        }

    def get_logs(self):
        log_path = os.path.join(get_app_path(), "login.log")
        if not os.path.exists(log_path):
            return []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return [l.strip() for l in lines[-30:]]
        except:
            return []

    def clear_logs(self):
        log_path = os.path.join(get_app_path(), "login.log")
        try:
            open(log_path, "w", encoding="utf-8").close()
            logger.log("日志已清空")
            return True
        except:
            return False

    def check_autostart(self):
        import subprocess
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            r = subprocess.run(
                ['schtasks', '/query', '/tn', 'BJTUAutoLogin'],
                capture_output=True, text=True, errors='replace',
                startupinfo=si)
            return r.returncode == 0
        except:
            return False

    def set_autostart(self, enabled):
        import subprocess
        task = 'BJTUAutoLogin'
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            if enabled:
                subprocess.run(['schtasks', '/delete', '/tn', task, '/f'],
                               capture_output=True, startupinfo=si)
                if getattr(sys, 'frozen', False):
                    exe = sys.executable
                    cmd = ['schtasks', '/create', '/tn', task,
                           '/tr', f'"{exe}"', '/sc', 'onlogon', '/f']
                else:
                    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                    script = os.path.join(get_app_path(), "src", "main.py")
                    cmd = ['schtasks', '/create', '/tn', task,
                           '/tr', f'"{pythonw}" "{script}"',
                           '/sc', 'onlogon', '/f']
                r = subprocess.run(cmd, capture_output=True, text=True,
                                   errors='replace', startupinfo=si)
                if r.returncode != 0:
                    raise RuntimeError(r.stderr.strip())
                logger.log("开机自启已开启")
            else:
                subprocess.run(['schtasks', '/delete', '/tn', task, '/f'],
                               capture_output=True, startupinfo=si)
                logger.log("开机自启已关闭")
            return True
        except Exception as e:
            logger.log(f"开机自启设置失败: {e}")
            return False

    def minimize(self):
        if self._app._window:
            self._app._window.minimize()

    def open_url(self, url):
        """在默认浏览器打开链接"""
        webbrowser.open(url)

    def open_log(self):
        """打开日志文件"""
        p = os.path.join(get_app_path(), "login.log")
        if os.path.exists(p):
            webbrowser.open(p)
            return True
        return False

    def maximize(self):
        if self._app._window:
            self._app._window.toggle_fullscreen()

    def close(self):
        self._app.running = False
        if self._app._window:
            self._app._window.destroy()
        os._exit(0)


# ========== 主应用 ==========

class AutoLoginApp:
    def __init__(self):
        self.cfg = self._load_config()
        self.portal = Portal(self.cfg["username"], self.cfg["password"])
        self.check_interval = self.cfg.get("check_interval", 60)
        self.retry_interval = self.cfg.get("retry_interval", 10)
        self.test_url = self.cfg["test_url"]
        self.running = True
        self.wifi_connected = False
        self.wifi_ssid = ""
        self.net_connected = False
        self._window = None

    def _load_config(self):
        try:
            config_path = get_config_path()
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"username": "", "password": "",
                    "check_interval": 60, "retry_interval": 10,
                    "test_url": "https://www.baidu.com"}

    def run_check_loop(self):
        time.sleep(5)
        while self.running:
            sleep_time = self.check_interval
            try:
                self.wifi_connected = is_wifi_connected()
                self.wifi_ssid = get_wifi_ssid() if self.wifi_connected else ""

                if not self.wifi_connected:
                    logger.log("WiFi未连接，等待连接...")
                    time.sleep(self.retry_interval)
                    continue

                self.net_connected = is_online(self.test_url)
                if self.net_connected:
                    time.sleep(sleep_time)
                    continue

                logger.log("检测到断网，开始认证...")
                success, message = self.portal.login()
                tag = "成功" if success else "失败"
                logger.log(f"登录{tag}：{message}")
                sleep_time = self.check_interval if success else self.retry_interval
            except Exception as e:
                logger.log(f"程序异常：{e}")
                sleep_time = self.retry_interval
            time.sleep(sleep_time)

    def start(self):
        logger.log("BJTU校园网自动登录程序启动")

        check_thread = threading.Thread(target=self.run_check_loop, daemon=True)
        check_thread.start()

        import webview

        html_path = get_resource_path(os.path.join("web", "index.html"))
        # PyWebView 某些版本对本地文件路径处理不稳定，统一用 file:// 协议
        if not html_path.startswith("file://"):
            html_path = "file:///" + html_path.replace("\\", "/")
        api = Api(self)

        self._window = webview.create_window(
            title="BJTU 校园网自动登录",
            url=html_path,
            js_api=api,
            width=960,
            height=680,
            min_size=(800, 720),
            frameless=True,
            easy_drag=True,
            background_color="#f5f7fa",
        )

        # 设置窗口图标
        icon_path = get_resource_path(os.path.join("resources", "icon.ico"))
        if os.path.exists(icon_path):
            _set_window_icon(self._window, icon_path)

        webview.start(debug=False)


def signal_handler(signum, frame):
    logger.log("收到退出信号")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    app = AutoLoginApp()
    app.start()
