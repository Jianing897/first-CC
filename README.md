# 🍅 番茄钟 - 桌面 Pomodoro Timer

一个简洁的 Windows 桌面番茄钟应用，基于 PowerShell + WPF 构建，无需安装任何额外依赖。

## ✨ 功能特性

- **🍅 番茄工作法**: 25分钟专注 → 5分钟短休 → 每4轮15分钟长休
- **📌 窗口置顶**: 始终在最前，不被打扰
- **📊 计数统计**: 自动记录每日完成的番茄数
- **🎵 完成提醒**: 计时结束后弹窗 + 提示音
- **⌨️ 键盘快捷键**: 无需鼠标点击即可操作
- **🎨 颜色区分**: 专注(红) / 短休(绿) / 长休(蓝)

## 🚀 使用方法

### 方式一：右键运行
在文件资源管理器中右键 `pomodoro.ps1` → **使用 PowerShell 运行**

### 方式二：命令行运行
```powershell
powershell -ExecutionPolicy Bypass -File pomodoro.ps1
```

### 方式三：创建快捷方式
1. 右键桌面 → 新建 → 快捷方式
2. 输入: `powershell -ExecutionPolicy Bypass -File "C:\Users\rbssh\first_CC\pomodoro.ps1"`
3. 双击快捷方式即可启动

## ⌨️ 快捷键

| 按键 | 功能 |
|------|------|
| `Space` | 开始 / 暂停 |
| `R` | 重置当前计时 |
| `S` | 跳过当前阶段 |
| `T` | 切换窗口置顶 |

## ⚙️ 时长配置

默认时长（可在脚本顶部修改）：
- 专注时间: 25 分钟
- 短休息: 5 分钟
- 长休息: 15 分钟

## 📁 数据存储

今日番茄计数保存在 `%LOCALAPPDATA%\PomodoroApp\today.json`，每天自动清零。

## 🔧 系统要求

- Windows 10 / 11
- PowerShell 5.1+ (系统自带，无需安装)
