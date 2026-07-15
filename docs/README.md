# BJTU校园网自动登录

北京交通大学校园网自动登录工具

## 功能特性

- ✅ 自动检测网络状态，断网自动登录
- ✅ 开机自动启动（通过 Windows 任务计划程序）
- ✅ 后台运行（无 CMD 黑框）
- ✅ 系统托盘图标
- ✅ 右键菜单（立即登录、查看日志、退出）
- ✅ 自动检测 WiFi 是否连接
- ✅ 运行日志记录

## 安装步骤

1. 确保已安装 Python 3.7+
2. 编辑 `config.json`，填入你的校园网账号和密码
3. 双击运行 `install.bat` 进行安装
4. 安装完成后程序会自动启动

## 配置说明

`config.json` 配置项：

```json
{
    "username": "你的学号",
    "password": "你的密码",
    "check_interval": 60,
    "retry_interval": 10,
    "test_url": "https://www.baidu.com"
}
```

- `check_interval: 正常状态检查间隔（秒）
- `retry_interval`: 失败后重试间隔（秒）

## 卸载

双击运行 `uninstall.bat` 卸载程序

## 手动运行

- 安装后会在桌面创建快捷方式
- 也可以直接运行 `pythonw main.pyw` 后台启动
- 或者运行 `python main.py` 有窗口调试模式
