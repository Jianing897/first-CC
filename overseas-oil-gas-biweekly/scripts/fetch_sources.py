#!/usr/bin/env python3
"""从登记信息源采集双周报素材，输出 items.json。

依赖：lxml（无 httpx/beautifulsoup4 亦可运行）
"""

import argparse
import json
import re
import sys
import time
import uuid
from datetime import date, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from lxml import html

from coverage_rules import (
    detect_country,
    detect_topics,
    is_likely_analysis,
    is_target_country,
)

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "references" / "sources.json"
USER_AGENT = "Mozilla/5.0 (compatible; CNOOC-Research-Bot/1.0; +internal-research)"
DATE_IN_URL = re.compile(r"/(\d{4})/(\d{1,2})/(\d{1,2})/")
OILPRICE_DATE = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})",
    re.I,
)
WORLD_OIL_DATE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})",
    re.I,
)
MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def fetch_html(url: str, retries: int = 3) -> bytes:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=45) as resp:
                return resp.read()
        except (URLError, TimeoutError, OSError) as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"无法获取 {url}: {last_err}")


def parse_date_from_url(url: str) -> date | None:
    m = DATE_IN_URL.search(url)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def parse_month_text(text: str) -> date | None:
    m = OILPRICE_DATE.search(text)
    if m:
        mo = MONTH_MAP[m.group(1).lower()[:3]]
        return date(int(m.group(3)), mo, int(m.group(2)))
    m = WORLD_OIL_DATE.search(text)
    if m:
        mo = MONTH_MAP[m.group(1).lower()]
        return date(int(m.group(3)), mo, int(m.group(2)))
    return None


def in_range(d: date | None, since: date | None, until: date | None) -> bool:
    if d is None:
        # 列表页条目常无 URL 日期（如 Oil Price），保留供成稿阶段核实
        return True
    if since and d < since:
        return False
    if until and d > until:
        return False
    return True


def make_item(
    source_cfg: dict,
    title: str,
    url: str,
    published: date | None,
    snippet: str,
    extra_tags: list[str] | None = None,
) -> dict:
    tags = list(source_cfg.get("topic_tags", []))
    if extra_tags:
        tags.extend(extra_tags)
    item = {
        "id": str(uuid.uuid4()),
        "fetched_at": date.today().isoformat(),
        "source_platform": source_cfg["source_platform"],
        "source_name": source_cfg["source_name"],
        "url": url,
        "title": title.strip(),
        "published": published.isoformat() if published else None,
        "snippet": snippet.strip()[:500],
        "region_hint": source_cfg.get("region_hint"),
        "topic_tags": sorted(set(tags)),
    }
    return enrich_item(item)


def enrich_item(item: dict) -> dict:
    text = f"{item['title']} {item.get('snippet', '')}"
    hint = item.get("region_hint")
    country = None
    if hint and hint in ("巴西", "中东", "埃及"):
        country = detect_country(text) or (hint if hint != "中东" else None)
    else:
        country = detect_country(text)
    if country:
        item["country"] = country
    item["topics"] = sorted(set(item.get("topics", []) + detect_topics(text)))
    item["likely_analysis"] = is_likely_analysis(item["title"], item.get("snippet", ""))
    item["in_target_countries"] = is_target_country(country)
    return item


def _oilprice_title_dates(tree: html.HtmlElement) -> dict[str, date]:
    mapping: dict[str, date] = {}
    for block in tree.xpath("//h2"):
        title = block.text_content().strip()
        if len(title) < 15:
            continue
        ctx = ""
        for el in block.xpath("following-sibling::*")[:4]:
            ctx += el.text_content() + "\n"
        d = parse_month_text(ctx)
        if d:
            mapping[title] = d
    return mapping


def parse_oilprice(tree: html.HtmlElement, source_cfg: dict) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    title_dates = _oilprice_title_dates(tree)

    for row in tree.xpath('//div[contains(@class,"headline_row")]'):
        link = row.xpath('.//a[@class="full_parent"]/@href')
        name = row.xpath('.//span[@class="article_name"]/text()')
        if not link or not name:
            continue
        url = link[0].strip()
        title = name[0].strip()
        if url in seen:
            continue
        seen.add(url)
        published = title_dates.get(title) or parse_date_from_url(url)
        items.append(make_item(source_cfg, title, url, published, ""))

    for block in tree.xpath('//h2'):
        title = block.text_content().strip()
        if len(title) < 15:
            continue
        parent = block.getparent()
        url = ""
        if parent is not None and parent.tag == "a" and parent.get("href"):
            url = urljoin(source_cfg["list_url"], parent.get("href"))
        ctx = ""
        following = block.xpath("following-sibling::*")
        for el in following[:3]:
            ctx += el.text_content() + "\n"
        if not url:
            m = re.search(
                r'href="(https://oilprice\.com/Latest-Energy-News/World-News/[^"#]+)"',
                html.tostring(block, encoding="unicode"),
            )
            if m:
                url = m.group(1)
        published = parse_month_text(ctx) or parse_date_from_url(url)
        snippet = ""
        for el in following:
            t = el.text_content().strip()
            if len(t) > 60 and "|" not in t[:30]:
                snippet = t
                break
        if url and url not in seen:
            seen.add(url)
            items.append(make_item(source_cfg, title, url, published, snippet))
    return items


def parse_worldoil(tree: html.HtmlElement, base_url: str, source_cfg: dict) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for a in tree.xpath("//a[h2]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        url = urljoin(base_url, href)
        if "/news/" not in url:
            continue
        h2 = a.xpath("h2")
        if not h2:
            continue
        title = h2[0].text_content().strip()
        parent = a.getparent()
        ctx = parent.text_content() if parent is not None else ""
        published = parse_month_text(ctx) or parse_date_from_url(url)
        if url in seen:
            continue
        seen.add(url)
        items.append(make_item(source_cfg, title, url, published, ""))
    return items


def parse_meobserver(tree: html.HtmlElement, base_url: str, source_cfg: dict) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    energy_kw = source_cfg.get("energy_path_keywords", [])

    for h3 in tree.xpath("//h3"):
        links = h3.xpath(".//a/@href")
        if not links:
            continue
        url = urljoin(base_url, links[0])
        if "meobserver.org" not in url or "/2026/" not in url and "/2025/" not in url:
            if not DATE_IN_URL.search(url):
                continue
        title = h3.text_content().strip()
        if len(title) < 20 or url in seen:
            continue
        path_lower = urlparse(url).path.lower()
        is_energy = any(kw in path_lower or kw in title.lower() for kw in energy_kw)
        tags = ["energy"] if is_energy else []
        if not is_energy and energy_kw:
            continue
        seen.add(url)
        published = parse_date_from_url(url)
        items.append(make_item(source_cfg, title, url, published, "", extra_tags=tags))
    return items


def parse_brazil_energy(tree: html.HtmlElement, base_url: str, source_cfg: dict) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()

    for heading in tree.xpath("//*[contains(@class,'entry-title')]"):
        links = heading.xpath(".//a/@href")
        if not links:
            continue
        href = links[0].strip()
        url = urljoin(base_url, href).split("#")[0]
        if "brazilenergyinsight.com" not in url or not DATE_IN_URL.search(url):
            continue
        title = heading.text_content().strip()
        if len(title) < 15 or url in seen:
            continue
        seen.add(url)
        published = parse_date_from_url(url)
        snippet = ""
        article = heading.xpath("ancestor::article[1]")
        if article:
            snippet = article[0].text_content().strip()[:500]
        items.append(make_item(source_cfg, title, url, published, snippet))
    return items


PARSERS = {
    "oilprice_world": parse_oilprice,
    "worldoil_news": lambda t, cfg: parse_worldoil(t, cfg["list_url"], cfg),
    "meobserver": lambda t, cfg: parse_meobserver(t, cfg["list_url"], cfg),
    "brazil_energy_insight": lambda t, cfg: parse_brazil_energy(t, cfg["list_url"], cfg),
}


def fetch_all(
    since: date | None,
    until: date | None,
    max_per_source: int,
    source_ids: list[str] | None,
    target_countries_only: bool = False,
    exclude_analysis: bool = True,
) -> list[dict]:
    with SOURCES_FILE.open(encoding="utf-8") as f:
        config = json.load(f)

    all_items: list[dict] = []
    for source_cfg in config["sources"]:
        sid = source_cfg["id"]
        if source_ids and sid not in source_ids:
            continue
        parser = PARSERS.get(sid)
        if not parser:
            print(f"跳过未知源: {sid}", file=sys.stderr)
            continue
        print(f"采集: {source_cfg['source_name']} …")
        raw = fetch_html(source_cfg["list_url"])
        tree = html.fromstring(raw)
        items = parser(tree, source_cfg)
        filtered = [it for it in items if in_range(
            date.fromisoformat(it["published"]) if it["published"] else None,
            since,
            until,
        )]
        if since or until:
            dated = [it for it in filtered if it["published"]]
            undated = [it for it in filtered if not it["published"]]
            filtered = dated + undated[: max(0, max_per_source - len(dated))]
        filtered = filtered[:max_per_source]
        print(f"  → {len(filtered)} 条（原始 {len(items)} 条）")
        all_items.extend(filtered)

    deduped: list[dict] = []
    seen_urls: set[str] = set()
    for it in all_items:
        u = it["url"]
        if u in seen_urls:
            continue
        seen_urls.add(u)
        deduped.append(it)
    deduped.sort(key=lambda x: x.get("published") or "", reverse=True)

    if exclude_analysis:
        deduped = [it for it in deduped if not it.get("likely_analysis")]
    if target_countries_only:
        deduped = [it for it in deduped if it.get("in_target_countries")]

    return deduped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="采集海外油气双周报信息源")
    parser.add_argument("--output", "-o", required=True, help="输出 items.json 路径")
    parser.add_argument("--since", help="起始日期 YYYY-MM-DD（含）")
    parser.add_argument("--until", help="结束日期 YYYY-MM-DD（含）")
    parser.add_argument("--max-per-source", type=int, default=30, help="每个源最多保留条数")
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="仅采集指定源 id（可多次指定），见 references/sources.json",
    )
    parser.add_argument(
        "--target-countries-only",
        action="store_true",
        help="仅保留 coverage_policy 清单内国别",
    )
    parser.add_argument(
        "--include-analysis",
        action="store_true",
        help="包含分析/预测类标题（默认排除）",
    )
    args = parser.parse_args(argv)

    since = date.fromisoformat(args.since) if args.since else None
    until = date.fromisoformat(args.until) if args.until else None

    items = fetch_all(
        since,
        until,
        args.max_per_source,
        args.sources,
        target_countries_only=args.target_countries_only,
        exclude_analysis=not args.include_analysis,
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "since": args.since,
        "until": args.until,
        "count": len(items),
        "items": items,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {len(items)} 条 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
