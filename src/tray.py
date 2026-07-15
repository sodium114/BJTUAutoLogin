import os
import sys
import threading
import webbrowser
import traceback

# 获取资源路径（兼容打包）
def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容 PyInstaller 打包"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_app_path():
    """获取应用程序所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None

try:
    import pystray
    from pystray import MenuItem as item
except ImportError:
    pystray = None
    item = None


def create_image():
    """创建托盘图标"""
    if Image is None:
        return None
    
    # 优先在应用程序目录查找，其次在 resources 文件夹查找，最后在资源目录查找
    icon_path = os.path.join(get_app_path(), "icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(get_app_path(), "resources", "icon.ico")
    if not os.path.exists(icon_path):
        icon_path = get_resource_path("icon.ico")
    
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except:
            pass
    
    try:
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color=(34, 139, 34))
        dc = ImageDraw.Draw(image)
        dc.text((15, 20), "BJTU", fill=(255, 255, 255))
        return image
    except:
        return None


class SystemTray:
    def __init__(self, on_login=None, on_exit=None, on_show=None):
        self.on_login = on_login
        self.on_exit = on_exit
        self.on_show = on_show
        self.icon = None
        self.thread = None
        self.available = (pystray is not None) and (Image is not None)

    def on_click_login(self, icon, item):
        """立即登录"""
        try:
            if self.on_login:
                self.on_login()
        except Exception as e:
            print(f"登录错误: {e}")

    def on_click_show(self, icon, item):
        """显示主窗口"""
        try:
            if self.on_show:
                self.on_show()
        except Exception as e:
            print(f"显示窗口错误: {e}")

    def on_click_view_log(self, icon, item):
        """查看日志"""
        try:
            log_path = os.path.join(get_app_path(), "login.log")
            if os.path.exists(log_path):
                webbrowser.open(log_path)
        except Exception as e:
            print(f"查看日志错误: {e}")

    def on_click_exit(self, icon, item):
        """退出程序"""
        try:
            if self.on_exit:
                self.on_exit()
            icon.stop()
        except Exception as e:
            print(f"退出错误: {e}")

    def run(self):
        """运行托盘图标"""
        if not self.available:
            print("警告：pystray或Pillow未安装，托盘功能不可用")
            return
        
        try:
            menu = pystray.Menu(
                item('显示主窗口', self.on_click_show, default=True),
                item('立即登录', self.on_click_login),
                item('查看日志', self.on_click_view_log),
                item('退出', self.on_click_exit)
            )
            
            image = create_image()
            if image is None:
                print("警告：无法创建托盘图标")
                return
            
            self.icon = pystray.Icon(
                "BJTUAutoLogin",
                image,
                "BJTU校园网自动登录",
                menu
            )
            
            self.icon.run()
        except Exception as e:
            print(f"托盘启动错误: {e}")
            traceback.print_exc()

    def start(self):
        """在新线程中启动托盘"""
        if not self.available:
            return
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        """停止托盘"""
        try:
            if self.icon:
                self.icon.stop()
        except:
            pass
