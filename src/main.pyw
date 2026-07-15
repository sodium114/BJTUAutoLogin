#!/usr/bin/env python3
"""BJTU 校园网自动登录 - 无控制台启动入口 (.pyw)

本文件是 main.py 的无窗口包装器。
双击此文件将以无控制台（后台）模式运行程序。
"""

import sys
import os

# 确保 src 目录在 path 中，以便导入同目录下的模块
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 从 main 模块导入所有逻辑并启动
from main import AutoLoginApp, signal_handler, logger
import signal

if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        app = AutoLoginApp()
        app.start()
    except KeyboardInterrupt:
        logger.log("程序被用户中断")
    except Exception as e:
        logger.log(f"程序异常退出: {e}")
        import traceback
        traceback.print_exc()
