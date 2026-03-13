# 斗地主游戏开发计划

## 项目概述
使用Python和Pygame开发一个画面精美的三人斗地主游戏，支持简体中文界面。

## 技术栈
- **语言**: Python 3.9+
- **图形库**: Pygame
- **打包工具**: PyInstaller
- **CI/CD**: GitHub Actions

## 开发阶段

### 第一阶段: 基础架构 (v0.1)
- [x] 创建项目结构
- [x] 配置日志系统
- [x] 实现扑克牌数据结构和基础操作
- [x] 实现斗地主核心规则（牌型判断、大小比较）

### 第二阶段: 游戏逻辑 (v0.2) - 已完成
- [x] 实现发牌和叫地主逻辑
- [x] 实现出牌验证逻辑
- [x] 实现游戏流程控制
- [x] 实现胜负判定和计分

### 第三阶段: UI界面 (v0.3) - 已完成
- [x] 设计并实现主菜单
- [x] 实现游戏主界面（牌桌、手牌显示）
- [x] 实现出牌交互
- [ ] 添加动画效果

### 第四阶段: AI对手 (v0.4) - 已完成
- [x] 实现基础AI策略
- [x] 实现智能出牌算法
- [ ] 优化AI决策逻辑

### 第五阶段: 完善优化 (v1.0)
- [ ] 添加音效和背景音乐
- [ ] 优化UI美观度
- [ ] 添加设置选项
- [ ] 完善文档和README

## 目录结构
```
three-player-poker-k25/
├── assets/                 # 游戏资源
│   ├── images/            # 图片资源（卡牌、背景、按钮等）
│   ├── sounds/            # 音效和背景音乐
│   └── fonts/             # 字体文件
├── src/                   # 源代码
│   ├── __init__.py
│   ├── main.py           # 程序入口
│   ├── game/             # 游戏核心逻辑
│   │   ├── __init__.py
│   │   ├── card.py       # 扑克牌定义
│   │   ├── deck.py       # 牌组管理
│   │   ├── rules.py      # 斗地主规则
│   │   ├── player.py     # 玩家类
│   │   └── game_state.py # 游戏状态管理
│   ├── ui/               # 用户界面
│   │   ├── __init__.py
│   │   ├── game_window.py # 游戏窗口
│   │   ├── components.py  # UI组件
│   │   └── renderer.py    # 渲染器
│   ├── ai/               # AI逻辑
│   │   ├── __init__.py
│   │   └── ai_player.py   # AI玩家实现
│   └── utils/            # 工具函数
│       ├── __init__.py
│       └── logger.py     # 日志工具
├── tests/                # 测试代码
├── .github/
│   └── workflows/        # GitHub Actions
│       └── release.yml
├── requirements.txt      # Python依赖
├── README.md            # 项目说明
├── plan.md              # 本开发计划
└── .gitignore           # Git忽略文件
```

## 版本规划

### v0.1.0 - 基础版本
- 基础项目结构和日志系统
- 扑克牌核心逻辑
- 基础UI框架

### v0.2.0 - 游戏逻辑完善
- 完整游戏流程
- 叫地主功能
- 出牌验证

### v0.3.0 - UI美化
- 精美卡牌和资源
- 动画效果
- 中文界面

### v0.4.0 - AI实现
- 智能AI对手
- 策略优化

### v1.0.0 - 正式版
- 完整功能
- 跨平台发布
- 文档完善

## 更新日志

### v0.1.4 (2026-03-13)
- 修复 PyInstaller 打包后模块导入问题 (main.py 路径处理)
- 修复日志文件路径问题，支持打包后环境
- 关闭 issue #1: v0.1.3启动报错

### v0.1.3 (2026-03-13)
- 修复 Windows 构建 artifact 路径问题
- 修复 GitHub Release 权限问题
- 完整实现跨平台构建和自动发布

### v0.1.2 (2026-03-13)
- 修复 assets 目录缺失导致的 PyInstaller 构建失败
- 添加 FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 环境变量

### v0.1.1 (2026-03-13)
- 修复 GitHub Actions 使用已弃用 action 的问题
- 修复 PlayerType 枚举比较逻辑错误
- 修复 AI 玩家 ID 获取逻辑错误
- 添加 assets 目录结构

### v0.1.0 (2026-03-13)
- 初始版本发布
- 实现基础架构和核心扑克牌逻辑
- 配置日志系统和CI/CD
