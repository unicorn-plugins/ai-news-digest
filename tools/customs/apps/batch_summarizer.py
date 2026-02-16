#!/usr/bin/env python3
"""
Batch Summarizer for AI News Digest

중복 제거된 뉴스들을 일괄적으로 요약 및 번역하는 도구.
"""

import sys
import json
from groq_summarizer import process_news_items


def main():
    """CLI 진입점"""
    if len(sys.argv) < 2:
        print("Usage: batch_summarizer.py <deduplicated_json_file>")
        sys.exit(1)

    try:
        # 입력 파일 읽기
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.loads(f.read())

        # items 추출
        if isinstance(data, dict) and 'items' in data:
            items = data['items']
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError("Invalid input format")

        # 배치 처리 (use_batch=True로 배치 모드 사용)
        result = process_news_items(items, use_batch=True, batch_size=5)

        # 결과 출력
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if not result['success']:
            sys.exit(1)

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()