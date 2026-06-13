---
name: overseas-oil-gas-biweekly
description: "生成《海外油气投资环境资讯》双周报：从 Oil Price、World Oil、ME Observer、Brazil Energy Insight 采集素材，按 20 国清单筛选已发生事件（管理体制/财税/招标/发现/能源计划/碳政策/地缘），每国合并为一条、每期 10 条、新闻时报体、每条 500 字内并附 URL，输出 Word。用户提及海外油气投资环境资讯、双周报、投资环境资讯、油气投资双周、第 X 期、国别油气政策或地缘事件汇编时必须使用本技能。"
---

# 海外油气投资环境资讯（双周报）

按固定格式生成「中国海油集团能源经济研究院发展与战略研究中心国际化发展研究室」双周报。

**同事安装**：见 [`INSTALL.md`](INSTALL.md)（Git 克隆 + 一键脚本 `scripts/install_skill.ps1`）。

## 技能安装路径

执行脚本前 **先 `cd` 到技能根目录**（本技能所有相对路径均以此为基准）：

| 环境 | 路径 |
|------|------|
| Claude Code（用户级） | `C:\Users\rbssh\.claude\skills\overseas-oil-gas-biweekly` |
| Cursor（用户级） | `C:\Users\rbssh\.cursor\skills\overseas-oil-gas-biweekly` |
| 项目源码（可选） | `C:\Users\rbssh\first_CC\overseas-oil-gas-biweekly` |

PowerShell 进入技能目录：

```powershell
cd $env:USERPROFILE\.claude\skills\overseas-oil-gas-biweekly
```

`reports/` 目录默认写在技能根目录下；若在用户项目中出稿，可将 `--output` 指到项目路径。

## 必读参考

| 文件 | 用途 |
|------|------|
| `references/coverage_policy.md` | **国别清单、主题范围、事实/分析过滤、10条合并规则** |
| `references/report_template.md` | 版式、JSON 字段、`source_urls`、字体与段落样式 |
| `references/writing_style.md` | 新闻时报体、500字、来源 URL |
| `references/source_catalog.md` | 信息源与采集命令 |
| `references/sample_issue60.docx` | **Word 排版唯一参照**（桌面样例第6期） |

## 核心要求（必守）

1. **主题**：以国别为主——管理体制、财税、招标、重要发现、油气能源计划、碳政策、地缘政治**已发生事件**。
2. **事实 only**：不收录分析、预测、机构展望（见 `coverage_policy.md` 过滤词）。
3. **国别**：仅 `coverage_policy.md` 清单内 20 国；每期 **10 条**，**每国一条**（多国素材合并）。
4. **篇幅**：每条正文 **≤500 汉字**；体裁为 **新闻时报体**（见 `writing_style.md`）。
5. **来源**：每条附 **完整 https 链接**（`source_urls`）；合并条列多个 URL。

## 前置依赖

```bash
pip install -r requirements.txt
```

或：`pip install python-docx lxml`

## 工作流程

### 第一步：确认期次与时段

- `issue`、`total_issue`、`date_range`、本期编辑
- 发文单位固定：`中国海洋石油集团能源经济研究院 发展与战略研究中心国际化发展研究室`

### 第二步：信息采集

```powershell
cd $env:USERPROFILE\.claude\skills\overseas-oil-gas-biweekly
python scripts/fetch_sources.py `
  --since 2026-05-29 --until 2026-06-12 `
  --target-countries-only `
  --output reports/2026-W24/raw/items.json
```

默认排除 `likely_analysis: true`。人工素材并入 `items` 数组时需含 `url`、`country`、`likely_analysis: false`。

### 第三步：选题、按国合并、成稿

1. 读取 `raw/items.json`，丢弃分析类与非目标国别。
2. **按 `country` 分组**；组内多条合并为一条正文（≤500 字）。
3. 从候选国中选出 **10 国**，区域尽量均衡（见 `coverage_policy.md`）。
4. 写 `summary`（10 条标题）与 `articles`（10 条正文 + `source_urls`）。
5. 运行校验：

```powershell
python scripts/validate_structured.py reports/2026-W24/structured.json
```

### 第四步：生成 Word

**必须**使用桌面样例模板（已同步至 `references/sample_issue60.docx`）：

```powershell
python scripts/build_docx.py `
  -i reports/2026-issue08/structured.json `
  -o reports/2026-issue08/海外油气投资环境资讯-2026年第8期（总第62期）.docx `
  -t references/sample_issue60.docx
```

版式要点（详见 `references/report_template.md`）：

- 页眉表：黑体；发文单位、期次/时段各两行；**文字颜色 RGB(0,0,253)**；**1.5 倍行距**
- `【本期摘要】`/`【主要内容】`：方正楷体简体 12pt 加粗（Normal Indent）
- 摘要条目：List Paragraph + 仿宋 12pt + **1.5 倍行距**
- 正文标题：Normal + 左缩进 0.74cm + 方正楷体简体加粗 + **1.5 倍行距**
- 正文段落：Normal Indent + 仿宋 + 首行缩进 2 字符 + **1.5 倍行距**
- 来源行、本期编辑：右对齐 + 仿宋 + **1.5 倍行距**

### 第五步：人工审校

- [ ] 恰好 10 条，国别无重复
- [ ] 每条 ≤500 字、新闻时报体、无预测表述
- [ ] 每条 `source_urls` 可打开且与事实一致
- [ ] 摘要与正文标题一致

## 成稿 Prompt（Agent 内部）

```
你是海油集团国际化战略研究室研究员。根据 items.json 写 structured.json。

硬约束：
- summary 与 articles 各 10 条，region 国别不重复
- 仅已发生事件；禁止预计/展望/分析师观点
- 主题：管理体制、财税、招标、发现、能源计划、碳政策、地缘事件
- 国别仅限 coverage_policy.md 清单
- 同一国多条素材合并为一条，正文合计 ≤500 汉字
- 新闻时报体：时间+主体+事实+数据，短句，少议论
- 每条 articles[].source_urls: [{name, url}, ...]，url 来自 items
- 中文；公司首次出现：中文（英文缩写）
```

## 目录约定

```
reports/{year}-W{week}/
  raw/items.json
  structured.json
  海外油气投资环境资讯-....docx
```
