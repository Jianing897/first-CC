"""选题覆盖范围、国别识别、分析类标题过滤。"""

import re
from typing import Optional

# 正文国别简称
TARGET_COUNTRIES: dict[str, list[str]] = {
    "美国": ["美国", "美方", "华盛顿", "u.s.", "us ", " united states", "america", "american"],
    "伊拉克": ["伊拉克", "iraq", "iraqi", "somо", "basra", "巴士拉"],
    "阿联酋": ["阿联酋", "阿布扎比", "uae", "abu dhabi", "adnoc", "dubai", "富查伊拉", "fujairah"],
    "卡塔尔": ["卡塔尔", "qatar", "qatari"],
    "阿曼": ["阿曼", "oman", "omani"],
    "哈萨克斯坦": ["哈萨克斯坦", "哈萨克", "kazakhstan", "kazakh", "田吉兹", "tengiz", "卡沙干", "kashagan", "caspian pipeline", "cpc"],
    "阿塞拜疆": ["阿塞拜疆", "azerbaijan", "azerbaijani", "baku"],
    "俄罗斯": ["俄罗斯", "俄方", "russia", "russian", "moscow", "rosneft", "gazprom", "novorossiysk", "新罗西斯克"],
    "巴西": ["巴西", "brazil", "brazilian", "petrobras", "里约", "santos basin", "盐下", "pre-salt", "桑托斯"],
    "圭亚那": ["圭亚那", "guyana", "stabroek"],
    "特立尼达和多巴哥": ["特立尼达", "多巴哥", "trinidad", "tobago"],
    "苏里南": ["苏里南", "suriname"],
    "阿根廷": ["阿根廷", "argentina", "argentinian", "vaca muerta"],
    "墨西哥": ["墨西哥", "mexico", "mexican", "pemex"],
    "印尼": ["印尼", "印度尼西亚", "indonesia", "indonesian"],
    "马来西亚": ["马来西亚", "马来", "malaysia", "malaysian", "petronas"],
    "阿尔及利亚": ["阿尔及利亚", "algeria", "algerian", "sonatrach"],
    "加蓬": ["加蓬", "gabon", "gabonese"],
    "纳米比亚": ["纳米比亚", "namibia", "namibian", "namcor"],
    "莫桑比克": ["莫桑比克", "mozambique", "mozambican", "coral south", "roviuma"],
}

TOPIC_PATTERNS: dict[str, list[str]] = {
    "regime": ["管理体制", "监管", "许可制度", "regulation", "regulator", "ministry", "authority", "national oil company", "reform"],
    "fiscal": ["税", "财税", "关税", "暴利税", "利润分成", "tax", "levy", "duty", "fiscal", "royalty", "subsidy"],
    "tender": ["招标", "投标", "中标", "授标", "tender", "bid", "auction", "lease sale", "round", "awarded", "contract"],
    "discovery": ["发现", "试油", "储量", "discovery", "discover", "found oil", "found gas", "wildcat", "appraisal"],
    "energy_plan": ["能源计划", "产量目标", "扩产", "减产", "energy plan", "production target", "output", "capacity", "pipeline", "fpso", "refinery"],
    "carbon": ["碳", "甲烷", "ccus", "ccs", "ets", "emission", "climate", "net zero", "carbon", "methane", "renewable mandate"],
    "geopolitical": ["制裁", "袭击", "冲突", "封锁", "停火", "战争", "sanction", "attack", "strike", "blockade", "ceasefire", "war", "drone", "missile", "hormuz", "霍尔木兹"],
}

ANALYSIS_EN = re.compile(
    r"\b(forecast|predicts?|prediction|outlook|expects?|expected|analyst|analysis|"
    r"estimate|projected|projection|scenario|bullish|bearish|recommend|"
    r"likely to|may hit|could hit|could reach|if .{3,30} (collapses?|escalates?)|"
    r"sees .{3,20} (above|below|through|at \$))\b",
    re.I,
)

ANALYSIS_CN = re.compile(
    r"(预计|预测|展望|分析认为|机构认为|或将|有望|可能达|或突破|若.*则|情景|策略|建议|"
    r"或升至|或跌破|上看|下探|看涨|看跌)"
)

EVENT_SIGNAL = re.compile(
    r"(签署|授予|批准|发现|中标|招标|袭击|停产|复产|制裁|通过|上调|下调|投产|投运|"
    r"signed|awarded|approved|discovery|sanction|attack|outage|resumes?|tender|bid|"
    r"grants?|passed|regulation|launched|opens?|closed|shutdown)",
    re.I,
)

ISSUE_ARTICLE_COUNT = 10
MAX_BODY_CHARS = 500


def detect_country(text: str) -> Optional[str]:
    lower = f" {text.lower()} "
    best: Optional[str] = None
    best_len = 0
    for country, aliases in TARGET_COUNTRIES.items():
        for alias in aliases:
            a = alias.lower()
            if a in lower or alias in text:
                if len(alias) > best_len:
                    best = country
                    best_len = len(alias)
    return best


def detect_topics(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for code, patterns in TOPIC_PATTERNS.items():
        for p in patterns:
            if p.lower() in lower or p in text:
                found.append(code)
                break
    return found


def is_likely_analysis(title: str, snippet: str = "") -> bool:
    combined = f"{title} {snippet}"
    if ANALYSIS_CN.search(combined):
        return True
    if ANALYSIS_EN.search(combined):
        return True
    # 纯价格预测标题且无事件信号
    price_hint = re.search(r"\$\d+|price|油价|brent|wti", combined, re.I)
    if price_hint and not EVENT_SIGNAL.search(combined):
        if re.search(r"hit|reach|soar|plunge|tumble|jump|spike", combined, re.I):
            return True
    return False


def is_target_country(country: Optional[str]) -> bool:
    return country is not None and country in TARGET_COUNTRIES


def count_chinese_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", text))
