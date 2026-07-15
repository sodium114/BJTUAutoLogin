import json
import time
import threading
import signal
import sys
import os
import ctypes

# 高DPI适配
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# 获取程序运行目录（兼容打包后的环境）
def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_path():
    """获取 config.json 的路径"""
    app_path = get_app_path()
    # 先尝试在程序目录找
    config_path = os.path.join(app_path, "config.json")
    if os.path.exists(config_path):
        return config_path
    # 再尝试在 resources 文件夹找
    config_path = os.path.join(app_path, "resources", "config.json")
    if os.path.exists(config_path):
        return config_path
    # 最后返回默认路径
    return os.path.join(app_path, "config.json")

try:
    from logger import logger
    from network import is_online, is_wifi_connected, SimpleTrafficMonitor
    from portal import Portal
except Exception as e:
    print(f"导入模块错误: {e}")
    import traceback
    traceback.print_exc()
    time.sleep(5)
    sys.exit(1)

# 可选的托盘功能
try:
    from tray import SystemTray
    TRAY_AVAILABLE = True
except Exception as e:
    print(f"托盘模块未加载: {e}")
    TRAY_AVAILABLE = False

# 可选的 GUI 功能
try:
    import gui
    GUI_AVAILABLE = True
except Exception as e:
    print(f"GUI 模块未加载: {e}")
    GUI_AVAILABLE = False


def load_config():
    try:
        config_path = get_config_path()
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置错误: {e}")
        raise


class AutoLoginApp:
    def __init__(self):
        self.cfg = load_config()
        self.portal = Portal(self.cfg["username"], self.cfg["password"])
        self.check_interval = self.cfg.get("check_interval", 60)
        self.retry_interval = self.cfg.get("retry_interval", 10)
        self.test_url = self.cfg["test_url"]
        self.running = True
        self.tray = None
        self.gui = None
        self.traffic_monitor = SimpleTrafficMonitor()
        self.wifi_connected = False
        self.net_connected = False
        
        self.traffic_monitor.start()
    
    def force_login(self):
        logger.log("手动触发登录...")
        success, message = self.portal.login()
        if success:
            logger.log(f"登录成功：{message}")
        else:
            logger.log(f"登录失败：{message}")
    
    def on_exit(self):
        self.running = False
        logger.log("程序正在退出...")
    
    def on_config_changed(self, new_config):
        """配置变更回调"""
        logger.log("检测到配置变更，更新登录信息...")
        self.cfg = new_config
        self.portal = Portal(self.cfg["username"], self.cfg["password"])
    
    def run_check_loop(self):
        # 启动后先等待几秒，等网络稳定再开始检测
        time.sleep(5)
        
        while self.running:
            sleep_time = self.check_interval
            
            try:
                self.wifi_connected = is_wifi_connected()
                
                if not self.wifi_connected:
                    logger.log("WiFi未连接，等待连接...")
                    time.sleep(self.retry_interval)
                    continue
                
                self.net_connected = is_online(self.test_url)
                
                if self.net_connected:
                    self.traffic_monitor.update_online_status(True)
                    time.sleep(sleep_time)
                    continue
                
                logger.log("检测到断网，开始认证...")
                
                success, message = self.portal.login()
                
                if success:
                    logger.log(f"登录成功：{message}")
                    sleep_time = self.check_interval
                else:
                    logger.log(f"登录失败：{message}")
                    sleep_time = self.retry_interval
                
            except Exception as e:
                logger.log(f"程序异常：{e}")
                import traceback
                traceback.print_exc()
                sleep_time = self.retry_interval
            
            self.traffic_monitor.tick()
            time.sleep(sleep_time)
    
    def run_gui(self):
        if not GUI_AVAILABLE:
            return
        
        try:
            import tkinter as tk
            from tkinter import ttk
            
            root = tk.Tk()
            self.gui = gui.MainWindow(root)
            
            # 连接回调
            self.gui._on_manual_login = self.force_login
            self.gui.minimize_to_tray = self._minimize_gui_to_tray
            self.gui.on_config_changed = self.on_config_changed
            
            # 启动定时更新 GUI
            self._update_gui_loop(root)
            
            root.protocol("WM_DELETE_WINDOW", self._on_gui_closing)
            root.mainloop()
        except Exception as e:
            print(f"GUI 运行错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_gui_loop(self, root):
        if not self.running:
            return
        
        if self.gui:
            # 更新状态
            self.gui.update_status(self.wifi_connected, self.net_connected)

        root.after(1000, lambda: self._update_gui_loop(root))
    
    def _minimize_gui_to_tray(self):
        if self.gui and self.gui.root:
            self.gui.root.withdraw()
            # 如果有托盘图标，可以在这里显示提示
    
    def _on_gui_closing(self):
        if self.gui and self.gui.root:
            self.gui.on_closing()
        self.on_exit()
        sys.exit(0)

    def _show_gui_window(self):
        """从托盘恢复显示主窗口"""
        if self.gui and self.gui.root:
            self.gui.root.deiconify()
            self.gui.root.lift()
            self.gui.root.focus_force()
    
    def start(self):
        logger.log("BJTU校园网自动登录程序启动")
        
        # 启动系统托盘（如果可用）
        if TRAY_AVAILABLE:
            try:
                self.tray = SystemTray(
                    on_login=self.force_login,
                    on_exit=self.on_exit,
                    on_show=self._show_gui_window
                )
                self.tray.start()
            except Exception as e:
                logger.log(f"托盘启动失败: {e}")
        
        # 启动检查循环（在后台线程）
        check_thread = threading.Thread(target=self.run_check_loop, daemon=True)
        check_thread.start()
        
        # 启动 GUI（在主线程）
        if GUI_AVAILABLE:
            self.run_gui()
        else:
            # 如果没有 GUI，就保持主程序运行
            while self.running:
                time.sleep(1)


def signal_handler(signum, frame):
    logger.log("收到退出信号")
    sys.exit(0)


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        app = AutoLoginApp()
        app.start()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"程序启动错误: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)
