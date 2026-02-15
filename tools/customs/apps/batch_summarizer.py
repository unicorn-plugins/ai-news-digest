#!/usr/bin/env python3
"""
Batch Summarizer for AI News Digest

중복 제거된 뉴스들을 일괄적으로 요약 및 번역하는 도구.
"""

import sys
import json
import time
from datetime import datetime
from typing import List, Dict
from groq_summarizer import summarize_and_translate, load_groq_config


def process_news_batch(items: List[Dict], api_key: str, model: str = "llama-3.1-8b-instant") -> Dict[str, any]:
    """뉴스 항목들을 일괄 요약/번역 처리"""
    processed_items = []
    failed_items = []

    print(f"뉴스 요약 시작: {len(items)}개 항목", file=sys.stderr)

    for i, item in enumerate(items, 1):
        print(f"처리 중 [{i}/{len(items)}]: {item['title'][:50]}...", file=sys.stderr)

        # 콘텐츠 준비
        content_to_summarize = f"""Title: {item['title']}
Source: {item.get('source', 'Unknown')}
Category: {item.get('category', 'Unknown')}

Content:
{item.get('content', 'No content available')}"""

        try:
            # 요약 및 번역 수행
            result = summarize_and_translate(
                content_to_summarize,
                api_key=api_key,
                model=model,
                max_retries=3
            )

            if result['success']:
                # 원본 항목에 요약 정보 추가
                processed_item = item.copy()
                processed_item['summary_ko'] = result.get('summary_ko', '')
                processed_item['full_summary'] = result.get('full_response', '')
                processed_item['summarized_at'] = datetime.now().isoformat()
                processed_items.append(processed_item)
                print(f"  ✓ 요약 완료", file=sys.stderr)
            else:
                failed_items.append({
                    'item': item,
                    'error': result.get('error', 'Unknown error')
                })
                print(f"  ✗ 요약 실패: {result.get('error', 'Unknown')}", file=sys.stderr)

        except Exception as e:
            failed_items.append({
                'item': item,
                'error': str(e)
            })
            print(f"  ✗ 처리 오류: {e}", file=sys.stderr)

        # API 레이트 리밋 회피를 위한 대기
        if i < len(items):
            time.sleep(0.5)  # 0.5초 대기

    return {
        "success": len(processed_items) > 0,
        "processed_at": datetime.now().isoformat(),
        "total_items": len(items),
        "processed_count": len(processed_items),
        "failed_count": len(failed_items),
        "items": processed_items,
        "failed_items": failed_items
    }


def main():
    """CLI 진입점"""
    if len(sys.argv) < 2:
        print("Usage: batch_summarizer.py <deduplicated_json_file>")
        sys.exit(1)

    try:
        # Groq API 설정 로드
        config = load_groq_config()

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

        # 배치 처리
        result = process_news_batch(
            items,
            api_key=config['api_key'],
            model=config.get('model', 'llama-3.1-8b-instant')
        )

        # 결과 출력
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if not result['success']:
            sys.exit(1)

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()