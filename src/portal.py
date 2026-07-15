import json
import random
import re
import socket

import requests

LOGIN = "http://login.bjtu.edu.cn:801/eportal/portal/login"


class Portal:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()

        return ip

    def login(self):

        ip = self.get_ip()

        params = {
            "callback": "dr1003",
            "login_method": "1",
            "user_account": self.username,
            "user_password": self.password,
            "wlan_user_ip": ip,
            "wlan_user_ipv6": "",
            "wlan_user_mac": "000000000000",
            "wlan_ac_ip": "",
            "wlan_ac_name": "",
            "jsVersion": "4.2.1",
            "terminal_type": "1",
            "lang": "zh-cn",
            "v": random.randint(1000, 9999)
        }

        try:
            r = self.session.get(
                LOGIN,
                params=params,
                timeout=10
            )

        except requests.RequestException as e:
            return False, f"网络异常：{e}"

        m = re.search(r"dr1003\((.*)\);?$", r.text)

        if not m:
            return False, "服务器返回格式错误"

        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            return False, "JSON解析失败"

        message = data.get("msg", "未知错误")

        if data.get("result") == 1:
            return True, message

        return False, message