# 海外油气投资环境双周报 — 安装说明

面向 **中国海油集团能源经济研究院 发展与战略研究中心国际化发展研究室** 同事。本技能用于在 Cursor 或 Claude Code 中自动生成《海外油气投资环境资讯》双周报 Word 稿。

---

## 一、环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11（脚本按 PowerShell 编写） |
| Python | 3.10 及以上（已加入 PATH，可用 `py -3` 或 `python`） |
| AI 工具 | **Cursor** 和/或 **Claude Code**（二选一或都用） |
| 网络 | 采集素材时需访问 Oil Price、World Oil 等外网 |

---

## 二、从 Git 获取技能包

### 2.1 克隆仓库

技能目录位于仓库内路径：

```
overseas-oil-gas-biweekly/
```

克隆示例（请替换为研究室实际仓库地址）：

```powershell
git clone git@github.com:Jianing897/first-CC.git
cd first-CC
```

若技能单独放在其他仓库，克隆后进入含 `SKILL.md` 的 `overseas-oil-gas-biweekly` 目录即可。

### 2.2 目录应包含的文件

安装前确认以下关键文件存在：

```
overseas-oil-gas-biweekly/
├── SKILL.md                          # 技能主说明（Agent 自动读取）
├── INSTALL.md                        # 本安装说明
├── requirements.txt                  # Python 依赖
├── scripts/
│   ├── install_skill.ps1             # 一键安装脚本
│   ├── fetch_sources.py              # 信息采集
│   ├── build_docx.py                 # 生成 Word
│   └── validate_structured.py        # 校验 structured.json
├── references/
│   ├── sample_issue60.docx           # Word 排版模板（必含）
│   ├── coverage_policy.md
│   ├── report_template.md
│   └── ...
└── examples/
    └── issue60_structured.json       # 结构化数据样例
```

> `reports/` 为每期成稿输出目录，**不入库**；首次使用时会自动创建。

---

## 三、安装到本机（推荐：一键脚本）

在 **仓库根目录**（含 `overseas-oil-gas-biweekly` 文件夹的目录）打开 PowerShell，执行：

```powershell
powershell -ExecutionPolicy Bypass -File overseas-oil-gas-biweekly\scripts\install_skill.ps1
```

默认会同时安装到：

| 工具 | 安装路径 |
|------|----------|
| Cursor | `%USERPROFILE%\.cursor\skills\overseas-oil-gas-biweekly` |
| Claude Code | `%USERPROFILE%\.claude\skills\overseas-oil-gas-biweekly` |

仅安装 Cursor：

```powershell
powershell -ExecutionPolicy Bypass -File overseas-oil-gas-biweekly\scripts\install_skill.ps1 -Target cursor
```

仅安装 Claude Code：

```powershell
powershell -ExecutionPolicy Bypass -File overseas-oil-gas-biweekly\scripts\install_skill.ps1 -Target claude
```

脚本会自动执行 `pip install -r requirements.txt`（脚本界面为英文，避免编码问题；详细说明见下文）。

---

## 四、手动安装（无法运行脚本时）

### 4.1 复制技能目录

将仓库中的 `overseas-oil-gas-biweekly` **整个文件夹**复制到：

- Cursor：`C:\Users\<用户名>\.cursor\skills\overseas-oil-gas-biweekly`
- Claude Code：`C:\Users\<用户名>\.claude\skills\overseas-oil-gas-biweekly`

若 `.cursor\skills` 或 `.claude\skills` 不存在，请先新建 `skills` 文件夹。

### 4.2 安装 Python 依赖

```powershell
cd $env:USERPROFILE\.cursor\skills\overseas-oil-gas-biweekly
py -3 -m pip install -r requirements.txt
```

---

## 五、安装验证

### 5.1 检查文件

```powershell
Test-Path "$env:USERPROFILE\.cursor\skills\overseas-oil-gas-biweekly\SKILL.md"
Test-Path "$env:USERPROFILE\.cursor\skills\overseas-oil-gas-biweekly\references\sample_issue60.docx"
```

两项均应返回 `True`。

### 5.2 试生成 Word（可选）

```powershell
cd $env:USERPROFILE\.cursor\skills\overseas-oil-gas-biweekly
py -3 scripts\validate_structured.py examples\issue60_structured.json
py -3 scripts\build_docx.py `
  -i examples\issue60_structured.json `
  -o reports\test\试生成.docx `
  -t references\sample_issue60.docx
```

打开 `reports\test\试生成.docx`，核对页眉蓝字（RGB 0,0,253）、1.5 倍行距、字体是否与第6期样例一致。

---

## 六、如何使用

安装并**重启 Cursor / Claude Code** 后，在对话中说：

```
生成2026年第8期，总第62期的海外油气投资环境双周报
时间范围为2026年4月25日至2026年5月7日
```

也可使用这些触发词：**海外油气投资环境资讯**、**双周报**、**投资环境资讯**、**油气投资双周**、**国别油气政策汇编** 等。

Agent 将按 `SKILL.md` 流程：采集素材 → 选题成稿 → 校验 → 生成 Word。

---

## 七、更新技能

研究室更新脚本或版式后，在仓库拉取最新代码：

```powershell
cd <仓库路径>
git pull
powershell -ExecutionPolicy Bypass -File overseas-oil-gas-biweekly\scripts\install_skill.ps1
```

重新运行安装脚本会**覆盖**本机技能目录，保留 `reports/` 中已有成稿（成稿在技能目录下，若需保留请先备份 `reports` 文件夹）。

---

## 八、常见问题

| 现象 | 处理 |
|------|------|
| Agent 不触发技能 | 确认 `SKILL.md` 在 `.cursor\skills\` 或 `.claude\skills\` 下；重启 IDE；对话中使用「双周报」等关键词 |
| `pip install` 失败 | 使用 `py -3 -m pip install ...`；必要时加 `--user` |
| Word 版式不对 | 生成时必须带 `-t references\sample_issue60.docx`；检查模板文件是否存在 |
| 采集 0 条素材 | 检查网络与日期参数；部分源站可能暂时不可用，可人工补充 `items.json` |
| 字体显示异常 | 需本机安装 **黑体、仿宋、方正楷体简体**（与第6期样例一致） |

---

## 九、维护与反馈

- **技能维护**：国际化发展研究室（脚本与 `references/` 变更通过 Git 提交）
- **期次成稿**：`reports/` 目录建议本地或共享盘保存，勿提交 Git
- **问题反馈**：向技能维护人说明期次、时段、报错信息或版式截图

---

*文档版本：与仓库 `overseas-oil-gas-biweekly` 技能包同步维护。*
