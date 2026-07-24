# BJTU 校园网自动登录

> 北京交通大学校园网自动登录工具 — 连接 WiFi 后自动认证，断网自动重连，基于 PyWebView 实现。

## 功能

- **自动登录** — 检测到校园网 WiFi 后自动完成 Portal 认证，断网自动重连
- **状态监控** — 实时显示 WiFi 连接状态、SSID 和网络连通性
- **GUI 界面** — PyWebView + HTML/CSS 实现窗口，支持拖拽移动和最小化
- **开机自启** — 通过 Windows 任务计划程序实现，程序内一键开关
- **日志记录** — 完整的登录日志，支持界面内查看和清空
- **一键打包** — PyInstaller 打包为独立 EXE，无需 Python 环境

## 技术栈

| 层级 | 技术 |
|------|------|
| GUI | [PyWebView](https://pywebview.flowrl.com/) |
| 前端 | HTML5 + CSS3 + Vanilla JS |
| 网络 | [Requests](https://requests.readthedocs.io/) |
| 打包 | [PyInstaller](https://pyinstaller.org/) |

## 项目结构

```
BJTUAutoLogin/
├── src/
│   ├── main.py              # 入口：PyWebView 窗口 + 自动检测循环
│   ├── portal.py            # 校园网 Portal 登录接口
│   ├── network.py           # 网络检测：WiFi 状态 / 外网连通性
│   ├── logger.py            # 日志模块 + 路径工具
│   └── web/
│       ├── index.html       # 界面布局
│       ├── script.js        # 前端逻辑 + API 交互
│       └── style.css        # 样式
├── resources/
│   └── config.json.example  # 配置文件模板
├── docs/README.md
├── build.bat                # 打包脚本
├── run_gui.bat              # 一键启动
└── requirements.txt
```

## 快速开始

**环境要求**：Python ≥ 3.7，Windows 10+

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动
python src/main.py
# 或双击 run_gui.bat
```

### 打包为 EXE

```bash
# 生成 spec 文件（首次）
pyinstaller --onefile --windowed --name BJTUAutoLogin src/main.py

# 后续打包
pyinstaller BJTUAutoLogin.spec --clean --noconfirm
# 或双击 build.bat
```

输出：`dist/BJTUAutoLogin.exe`

## 配置

首次运行自动生成 `config.json`，也可从 `resources/config.json.example` 复制：

```json
{
    "username": "你的学号",
    "password": "你的密码",
    "check_interval": 60,
    "retry_interval": 10,
    "test_url": "https://www.baidu.com",
    "close_action": "ask",
    "close_remember": false,
    "taskbar_pinned": false
}
```

| 配置项 | 类型 | 默认 | 说明 |
|--------|------|------|------|
| `username` | string | — | 校园网账号（学号） |
| `password` | string | — | 校园网密码 |
| `check_interval` | int | `60` | 在线时检查间隔（秒） |
| `retry_interval` | int | `10` | 失败后重试间隔（秒） |
| `test_url` | string | `https://www.baidu.com` | 外网连通性测试地址 |
| `close_action` | string | `ask` | 关闭行为：`ask` 询问 / `minimize` 最小化 / `exit` 退出 |
| `close_remember` | bool | `false` | 记住关闭选择 |
| `taskbar_pinned` | bool | `false` | 任务栏固定状态 |

## 常见问题

**Q: WiFi 已连接但提示未连接？**  
A: WiFi 检测依赖 `netsh wlan show interfaces`，确保以普通用户权限运行即可。

**Q: 登录失败？**  
A: 确认账号密码正确，且当前连接的是 BJTU 校园网 WiFi（非其他网络或热点）。
