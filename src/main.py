#!/usr/bin/env python3
"""
斗地主游戏 - 主程序入口
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ui.game_window import main

if __name__ == "__main__":
    main()
