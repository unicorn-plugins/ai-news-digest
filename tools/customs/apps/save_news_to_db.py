#!/usr/bin/env python3
"""
Save News to Database

처리된 뉴스 항목들을 PostgreSQL 데이터베이스에 저장하는 도구.
"""

import sys
import json
from datetime import datetime
from db_client import DatabaseClient


def save_news_items(items: list, db_client: DatabaseClient) -> dict:
    """뉴스 항목들을 데이터베이스에 저장"""
    saved_count = 0
    failed_count = 0
    errors = []

    for item in items:
        # news_items 테이블에 저장
        insert_query = """
        INSERT INTO news_items (
            title, url, summary, summary_ko, category, source,
            published_at, collected_at, processed
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, true
        ) ON CONFLICT (url) DO UPDATE SET
            summary = EXCLUDED.summary,
            summary_ko = EXCLUDED.summary_ko,
            collected_at = EXCLUDED.collected_at,
            processed = true
        RETURNING id
        """

        # content를 summary 필드에 저장
        params = (
            item['title'],
            item['url'],
            item.get('content', '')[:500],  # 원본 내용 일부를 summary로 저장
            item.get('summary_ko', ''),
            item.get('category', 'Unknown'),
            item.get('source', 'Unknown'),
            item.get('published_at', datetime.now().isoformat()),
            datetime.now()
        )

        result = db_client.execute_query(insert_query, params, fetch="one")

        if result['success']:
            saved_count += 1
            print(f"✓ Saved: {item['title'][:50]}...", file=sys.stderr)
        else:
            failed_count += 1
            errors.append({
                'title': item['title'],
                'error': result.get('error', 'Unknown error')
            })
            print(f"✗ Failed: {item['title'][:50]}... - {result.get('error')}", file=sys.stderr)

    return {
        'success': saved_count > 0,
        'saved_count': saved_count,
        'failed_count': failed_count,
        'errors': errors
    }


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: save_news_to_db.py <processed_news_json>")
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

        # 데이터베이스 클라이언트 생성
        db_client = DatabaseClient()

        if not db_client.connect():
            print(json.dumps({
                'success': False,
                'error': 'Failed to connect to database'
            }))
            sys.exit(1)

        # 뉴스 항목 저장
        result = save_news_items(items, db_client)

        # 결과 출력
        result['timestamp'] = datetime.now().isoformat()
        result['total_items'] = len(items)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 연결 해제
        db_client.disconnect()

        if not result['success']:
            sys.exit(1)

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()