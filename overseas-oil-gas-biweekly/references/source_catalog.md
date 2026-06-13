# 信息来源目录

采集脚本读取 `references/sources.json`；成稿时 `source_name` 与下表「正文登记名」一致。

## 固定信息源（已接入采集脚本）

| id | 正文登记名 | 列表页 | 侧重 |
|----|-----------|--------|------|
| `oilprice_world` | Oil Price | https://oilprice.com/Latest-Energy-News/World-News/ | 全球油气要闻、地缘、油价 |
| `worldoil_news` | World Oil | https://www.worldoil.com/news | 上游项目、合同、深海工程 |
| `meobserver` | ME Observer | https://meobserver.org/ | 中东能源、埃及油气与基础设施 |
| `brazil_energy_insight` | Brazil Energy Insight | https://brazilenergyinsight.com/ | 巴西离岸油气、FPSO、盐下 |

### 正文来源写法

| 平台 | 样例写法 | 双周报 `source` 字段 |
|------|----------|---------------------|
| Oil Price | （信息来源：Oil Price） | `Oil Price` |
| World Oil | （信息来源：World Oil） | `World Oil` |
| ME Observer | （信息来源：ME Observer） | `ME Observer` |
| Brazil Energy Insight | （信息来源：Brazil Energy Insight） | `Brazil Energy Insight` |
| 彭博 | 彭博消息 / 彭博社 X 月 X 日消息 | `彭博`（样例第 60 期，暂无自动采集） |

ME Observer 采集默认过滤能源相关路径/标题（oil、gas、energy、LNG、pipeline 等）；中东政经类非能源稿不进入 `items.json`。

## 采集命令

```bash
# 推荐：双周窗口 + 目标国别 + 排除分析预测类标题
python overseas-oil-gas-biweekly/scripts/fetch_sources.py \
  --since 2026-05-29 \
  --until 2026-06-12 \
  --target-countries-only \
  --output overseas-oil-gas-biweekly/reports/2026-W24/raw/items.json

# 仅采 Oil Price + World Oil
python overseas-oil-gas-biweekly/scripts/fetch_sources.py \
  --source oilprice_world --source worldoil_news \
  --target-countries-only \
  --output reports/raw/items.json
```

采集结果字段补充：`country`、`topics`、`likely_analysis`、`in_target_countries`（见 `coverage_policy.md`）。

## 建议扩展来源（尚未接入）

| 登记名 | 用途 | 备注 |
|--------|------|------|
| 彭博 | 出口通道、长期供气协议 | 需订阅或人工导出 |
| Reuters Energy | 交易、制裁、出口 | 需订阅 |
| 公司 Newsroom | Shell、TotalEnergies、ADNOC、Petrobras 等 | RSS 或新闻稿页 |

## 国别/主题关键词（选题辅助）

```
霍尔木兹, Hormuz, 原油出口, crude export, FPSO, subsea, SURF,
LNG, 盐下, pre-salt, CPC pipeline, ADNOC, Petrobras,
地缘, sanctions, 减产, outage, drone attack
```

## 采集输出字段（items.json）

```json
{
  "generated_at": "2026-06-12T16:30:00",
  "since": "2026-05-29",
  "until": "2026-06-12",
  "count": 42,
  "items": [
    {
      "id": "uuid",
      "fetched_at": "2026-06-12",
      "source_platform": "Oil Price",
      "source_name": "Oil Price",
      "url": "https://...",
      "title": "英文标题",
      "published": "2026-06-12",
      "snippet": "摘要或首段",
      "region_hint": "巴西",
      "topic_tags": ["offshore", "fpso"]
    }
  ]
}
```

## 成稿约束

1. 正文事实必须能对应 `items.json` 中的 `url`。
2. 无可靠来源的条目不得写入正文。
3. 数字、日期以一手来源为准；二手媒体需交叉验证。
