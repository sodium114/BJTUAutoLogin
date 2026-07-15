import os
import sys
from datetime import datetime


def get_app_path():
    """获取应用程序所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Logger:

    def __init__(self):
        self.last_message = None
        self.log_path = os.path.join(get_app_path(), "login.log")

    def log(self, message):

        if message == self.last_message:
            return

        self.last_message = message

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        line = f"[{now}] {message}"

        print(line)

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except:
            pass


logger = Logger()