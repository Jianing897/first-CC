#!/usr/bin/env python3
"""校验 structured.json：10 条、字数、来源链接、国别唯一性。"""

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from coverage_rules import ISSUE_ARTICLE_COUNT, MAX_BODY_CHARS, count_chinese_chars


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="structured.json 路径")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    summary = data.get("summary", [])
    articles = data.get("articles", [])
    if len(summary) != ISSUE_ARTICLE_COUNT:
        errors.append(f"摘要须 {ISSUE_ARTICLE_COUNT} 条，当前 {len(summary)}")
    if len(articles) != ISSUE_ARTICLE_COUNT:
        errors.append(f"正文须 {ISSUE_ARTICLE_COUNT} 条，当前 {len(articles)}")

    regions = [a.get("region") for a in articles]
    if len(regions) != len(set(regions)):
        errors.append("正文存在重复国别，每期每国仅一条")

    for i, (s, a) in enumerate(zip(summary, articles), 1):
        if s.get("region") != a.get("region") or s.get("title") != a.get("title"):
            warnings.append(f"第 {i} 条摘要与正文标题不一致")
        body = "".join(a.get("paragraphs", []))
        n = count_chinese_chars(body)
        if n > MAX_BODY_CHARS:
            errors.append(f"第 {i} 条正文 {n} 字，超过 {MAX_BODY_CHARS}")
        if not a.get("source_urls"):
            errors.append(f"第 {i} 条缺少 source_urls")
        for su in a.get("source_urls", []):
            u = su.get("url", "")
            if not u.startswith("http"):
                errors.append(f"第 {i} 条来源 URL 无效: {u}")

    for msg in warnings:
        print(f"警告: {msg}")
    for msg in errors:
        print(f"错误: {msg}", file=sys.stderr)

    if errors:
        return 1
    print("校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
