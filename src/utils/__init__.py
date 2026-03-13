"""
日志工具模块
提供统一的日志配置和记录功能
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "doudizhu", level: int = logging.DEBUG) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建日志目录
    log_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # 生成日志文件名（按日期）
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_format)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"日志系统初始化完成，日志文件: {log_file}")
    return logger


def get_logger(name: str = "doudizhu") -> logging.Logger:
    """
    获取已配置的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)
