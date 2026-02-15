#!/usr/bin/env python3
"""
RSS Collector for AI News Digest

9개 RSS 피드에서 24시간 이내 AI 뉴스를 수집하고 파싱하는 도구.
"""

import sys
import json
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import urllib.parse


# RSS 피드 목록 (카테고리별로 분류)
RSS_FEEDS = {
    "연구 트렌드": [
        {
            "name": "arxiv cs.AI",
            "url": "https://arxiv.org/rss/cs.AI",
            "source": "arxiv cs.AI"
        },
        {
            "name": "arxiv cs.LG",
            "url": "https://arxiv.org/rss/cs.LG",
            "source": "arxiv cs.LG"
        }
    ],
    "빅테크 트렌드": [
        {
            "name": "Anthropic Blog",
            "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
            "source": "Anthropic Blog"
        },
        {
            "name": "Google AI Blog",
            "url": "https://blog.google/technology/ai/rss/",
            "source": "Google AI Blog"
        },
        {
            "name": "OpenAI Blog",
            "url": "https://openai.com/blog/rss.xml",
            "source": "OpenAI Blog"
        }
    ],
    "산업 뉴스": [
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/feed/",
            "source": "TechCrunch"
        },
        {
            "name": "VentureBeat",
            "url": "https://venturebeat.com/category/ai/feed/",
            "source": "VentureBeat"
        },
        {
            "name": "Hugging Face Daily Papers",
            "url": "https://huggingface.co/blog/feed.xml",
            "source": "Hugging Face"
        }
    ],
    "개발 실무": [
        {
            "name": "LangChain Blog",
            "url": "https://blog.langchain.dev/rss/",
            "source": "LangChain Blog"
        },
        {
            "name": "InfoQ",
            "url": "https://feed.infoq.com/ai-ml-data-eng/",
            "source": "InfoQ"
        }
    ]
}


def parse_feed_date(entry) -> datetime:
    """RSS 엔트리의 날짜를 파싱하여 datetime 객체로 변환"""
    # feedparser가 제공하는 parsed time 사용
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        import time
        return datetime(*entry.published_parsed[:6])
    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        import time
        return datetime(*entry.updated_parsed[:6])
    else:
        # fallback: 현재 시간 사용
        return datetime.now()


def fetch_feed(feed_info: Dict[str, str], category: str) -> List[Dict]:
    """단일 RSS 피드에서 뉴스 수집"""
    try:
        # User-Agent 헤더 추가로 차단 방지
        headers = {
            'User-Agent': 'AI News Digest Bot 1.0'
        }

        response = requests.get(feed_info['url'], headers=headers, timeout=30)
        response.raise_for_status()

        # feedparser로 파싱
        feed = feedparser.parse(response.content)

        if not feed.entries:
            print(f"Warning: No entries found in feed {feed_info['name']}", file=sys.stderr)
            return []

        # 24시간 이내 항목만 필터링
        now = datetime.now()
        cutoff_time = now - timedelta(hours=24)

        news_items = []
        for entry in feed.entries:
            published_at = parse_feed_date(entry)

            # 24시간 이내 항목만 선택
            if published_at < cutoff_time:
                continue

            # 필수 필드 검증
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()

            if not title or not link:
                continue

            # 본문 추출 (summary, content 등에서)
            content = ''
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value
            elif hasattr(entry, 'description'):
                content = entry.description

            news_item = {
                'title': title,
                'url': link,
                'published_at': published_at.isoformat(),
                'content': content,
                'category': category,
                'source': feed_info['source']
            }
            news_items.append(news_item)

        return news_items

    except requests.RequestException as e:
        print(f"Error fetching feed {feed_info['name']}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error parsing feed {feed_info['name']}: {e}", file=sys.stderr)
        return []


def collect_feeds() -> Dict[str, any]:
    """모든 RSS 피드에서 뉴스 수집"""
    collected_at = datetime.now().isoformat()
    all_items = []
    failed_feeds = []
    statistics = {"by_category": {}}

    print("RSS 피드 수집 시작...", file=sys.stderr)

    # 각 카테고리별로 피드 수집
    for category, feeds in RSS_FEEDS.items():
        category_count = 0

        for feed_info in feeds:
            print(f"수집 중: {feed_info['name']}", file=sys.stderr)
            items = fetch_feed(feed_info, category)

            if items:
                all_items.extend(items)
                category_count += len(items)
                print(f"수집 완료: {feed_info['name']} ({len(items)}개)", file=sys.stderr)
            else:
                failed_feeds.append(feed_info['name'])
                print(f"수집 실패: {feed_info['name']}", file=sys.stderr)

        statistics["by_category"][category] = category_count

    # 수집 통계 생성
    total_items = len(all_items)

    result = {
        "success": total_items > 0,
        "collected_at": collected_at,
        "total_items": total_items,
        "items": all_items,
        "statistics": {
            "by_category": statistics["by_category"],
            "failed_feeds": failed_feeds
        }
    }

    print(f"수집 완료: 총 {total_items}개 뉴스, 실패 {len(failed_feeds)}개 피드", file=sys.stderr)

    return result


def main():
    """CLI 진입점"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("RSS Collector for AI News Digest")
        print("Usage: rss_collector.py")
        print("Collects news from 9 RSS feeds within the last 24 hours")
        return

    try:
        result = collect_feeds()
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if not result["success"]:
            print("Error: 뉴스 수집에 실패했습니다.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "collected_at": datetime.now().isoformat(),
            "total_items": 0,
            "items": [],
            "statistics": {"by_category": {}, "failed_feeds": []}
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()