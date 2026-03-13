# 斗地主 (Doudizhu)

[![Build Status](https://github.com/ganecheng-ai/three-player-poker-k25/workflows/release.yml/badge.svg)](https://github.com/ganecheng-ai/three-player-poker-k25/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)

一款使用Python和Pygame开发的精美三人斗地主游戏，支持简体中文界面。

## 功能特点

- 经典斗地主玩法，支持1名玩家对2名AI
- 精美的游戏界面，支持卡牌动画效果
- 完整的音效系统（发牌、出牌、胜利、炸弹等）
- 智能AI对手，具有不同难度级别
- 完整的叫分、出牌、计分系统
- 支持顺子、连对、飞机、炸弹等各种牌型
- 游戏日志记录，方便问题排查
- 跨平台支持（Windows、Linux、macOS）

## 游戏规则

斗地主是一款流行的中国扑克牌游戏：

1. **发牌**：使用54张牌（含大小王），每人17张，留3张底牌
2. **叫分**：玩家可以选择叫1-3分成为地主，或选择不叫
3. **确定角色**：叫分最高者成为地主，获得底牌（共20张），其他两人为农民
4. **出牌**：地主先出牌，玩家按逆时针顺序轮流出牌
5. **胜利条件**：
   - 地主：出完所有手牌获胜
   - 农民：任一农民出完所有手牌，农民方获胜

### 牌型说明

| 牌型 | 说明 | 示例 |
|------|------|------|
| 单张 | 任意单牌 | ♠3 |
| 对子 | 两张相同点数的牌 | ♠3♥3 |
| 三张 | 三张相同点数的牌 | ♠3♥3♣3 |
| 三带一 | 三张 + 一张单牌 | ♠3♥3♣3 + ♠4 |
| 三带二 | 三张 + 一对 | ♠3♥3♣3 + ♠4♥4 |
| 顺子 | 5张以上连续单牌 | ♠3♥4♣5♦6♠7 |
| 连对 | 3对以上连续对子 | ♠3♥3 + ♣4♦4 + ♠5♥5 |
| 飞机 | 2组以上连续三张 | ♠3♥3♣3 + ♦4♠4♥4 |
| 炸弹 | 四张相同点数的牌 | ♠3♥3♣3♦3 |
| 火箭 | 大王 + 小王 | 大王 + 小王 |

### 牌型大小

- 火箭 > 炸弹 > 其他牌型
- 炸弹之间比较点数
- 其他牌型需同类型比较，点数大者胜

## 安装说明

### 从源码运行

#### 环境要求

- Python 3.9 或更高版本
- Pygame 2.5.0 或更高版本

#### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/ganecheng-ai/three-player-poker-k25.git
cd three-player-poker-k25
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行游戏
```bash
python src/main.py
```

### 预编译版本

从 [Releases](https://github.com/ganecheng-ai/three-player-poker-k25/releases) 页面下载对应平台的安装包：

- **Windows**: 下载 `doudizhu-windows-x64.exe`
- **Linux**: 下载 `doudizhu-linux-x64.tar.gz`
- **macOS**: 下载 `doudizhu-macos-x64.dmg`

## 游戏特性

### 音效系统

游戏包含丰富的音效：
- 发牌音效
- 出牌音效
- 过牌音效
- 叫分音效
- 选牌音效
- 炸弹特效音效
- 火箭特效音效
- 胜利/失败音效

### 动画效果

游戏包含流畅的动画：
- 发牌动画
- 出牌动画
- 卡牌选中高亮
- 炸弹/火箭粒子特效

## 操作说明

### 游戏界面

- **主菜单**：开始游戏或退出
- **叫分阶段**：选择叫分（1-3分）或不叫
- **游戏界面**：
  - 底部：你的手牌，点击选择要出的牌
  - 左右两侧：AI玩家信息和剩余牌数
  - 中央：出牌区域和底牌
  - 底部按钮：出牌、过牌、提示

### 键盘快捷键

- `ESC`：返回主菜单 / 退出游戏

## 项目结构

```
three-player-poker-k25/
├── assets/                 # 游戏资源
│   ├── images/            # 图片资源
│   ├── sounds/            # 音效和音乐
│   └── fonts/             # 字体文件
├── src/                   # 源代码
│   ├── main.py           # 程序入口
│   ├── game/             # 游戏核心逻辑
│   │   ├── card.py       # 扑克牌定义
│   │   ├── deck.py       # 牌组管理
│   │   ├── rules.py      # 斗地主规则
│   │   ├── player.py     # 玩家类
│   │   └── game_state.py # 游戏状态管理
│   ├── ui/               # 用户界面
│   │   ├── game_window.py # Pygame界面
│   │   └── animation.py   # 动画系统
│   ├── ai/               # AI逻辑
│   │   └── ai_player.py  # AI玩家实现
│   └── utils/            # 工具函数
│       ├── __init__.py   # 日志工具
│       └── sound.py      # 音效管理
├── tests/                # 测试代码
├── .github/workflows/    # CI/CD配置
│   └── release.yml       # 自动构建发布
├── requirements.txt      # Python依赖
├── README.md            # 项目说明
├── plan.md              # 开发计划
└── prompt.md            # 指令文件
```

## 开发计划

详见 [plan.md](plan.md)

### 当前版本

**v0.3.0** - AI优化版本
- 优化AI决策逻辑，支持多难度级别
- 增强手牌分析和策略选择

### 历史版本

**v0.2.1** - Bug修复版本
- 修复动画模块中 `pygame.random` 使用错误

**v0.2.0** - 音效动画版本
- 添加音效系统（发牌、出牌、胜利、炸弹等音效）
- 添加动画系统（出牌动画、粒子特效）
- 优化游戏交互体验

**v0.1.4** - 启动修复版本
- 修复 PyInstaller 打包后模块导入问题
- 修复日志文件路径问题，支持打包后环境
- 确保可执行文件能在各平台正常运行

**v0.1.3** - 构建流程修复版本
- 修复 Windows 构建 artifact 路径问题
- 修复 GitHub Release 权限问题
- 完整实现跨平台构建和自动发布

**v0.1.1** - 问题修复版本
- 修复 GitHub Actions workflow 使用已弃用 action 的问题
- 修复 PlayerType 枚举比较逻辑
- 修复 AI 玩家 ID 获取逻辑

**v0.1.0** - 基础版本
- 基础项目结构和日志系统
- 扑克牌核心逻辑
- 基础UI框架
- 简单AI对手

### 未来版本

- v0.3.0：增强AI智能，优化出牌策略
- v0.4.0：添加设置选项，支持音量调节
- v1.0.0：完整功能，正式发布

## 技术栈

- **Python 3.9+**：主要开发语言
- **Pygame 2.5+**：游戏图形库
- **PyInstaller 6.0+**：打包工具
- **GitHub Actions**：CI/CD

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

## 更新日志

### v0.3.0 (2026-03-13)
- 优化AI决策逻辑，支持多难度级别（简单/普通/困难）
- 添加手牌结构分析功能，智能识别孤牌、对子、三张、炸弹
- 增强手牌强度评估算法，考虑顺子、大牌数量、牌型完整性
- 优化第一手出牌策略，优先出难以组合的小牌
- 优化回应策略，更智能的队友识别和压牌决策
- 根据难度调整炸弹使用概率

### v0.2.1 (2026-03-13)
- 修复动画模块中 `pygame.random` 使用错误（应使用 Python 标准库 `random`）
- 修复炸弹和火箭特效中的随机数生成问题

### v0.2.0 (2026-03-13)
- 添加音效系统（发牌、出牌、胜利、炸弹等音效）
- 添加动画系统（出牌动画、粒子特效）
- 优化游戏交互体验

### v0.1.4 (2026-03-13)
- 修复 PyInstaller 打包后模块导入问题
- 修复日志文件路径问题，支持打包后环境
- 确保可执行文件能在各平台正常运行

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
- 基础Pygame界面实现
- 简单AI对手

## 联系方式

如有问题或建议，欢迎通过GitHub Issue反馈。

---

**斗地主** - 一款经典的中国扑克游戏，现在用Python重新演绎！
