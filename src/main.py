#!/usr/bin/env python3
"""
斗地主游戏 - 主程序入口
"""

import sys
import os

# 处理 PyInstaller 打包后的路径
if getattr(sys, 'frozen', False):
    # 打包后的运行环境
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录到路径
sys.path.insert(0, BASE_DIR)

from src.ui.game_window import main

if __name__ == "__main__":
    main()
