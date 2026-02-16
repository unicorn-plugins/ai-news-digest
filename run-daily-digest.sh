#!/bin/bash

# AI News Digest Daily Runner
# 매일 오전 8시에 실행되어 뉴스레터를 발행합니다.

set -e

PROJECT_DIR="/Users/dreamondal/workspace/ai-news-digest"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/daily-digest-$(date +%Y%m%d-%H%M%S).log"

mkdir -p "$LOG_DIR"

echo "========================================" | tee -a "$LOG_FILE"
echo "AI News Digest - Daily Run" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

source .venv/bin/activate

python3 << 'PYTHON_SCRIPT' 2>&1 | tee -a "$LOG_FILE"
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, '/Users/dreamondal/workspace/ai-news-digest')
os.chdir('/Users/dreamondal/workspace/ai-news-digest')

from tools.customs.apps.rss_collector import collect_feeds
from tools.customs.apps.duplicate_checker import remove_duplicates
from tools.customs.apps.groq_summarizer import process_news_items
from tools.customs.apps.db_client import DatabaseClient
from tools.customs.apps.newsletter_generator import generate_newsletter
from tools.customs.apps.email_sender import send_newsletter, send_error_notification

try:
    print("\n=== Phase 1: RSS 수집 ===")
    collect_result = collect_feeds()
    if not collect_result['success']:
        raise Exception("RSS 수집 실패")
    items = collect_result['items']
    print(f"수집 완료: {len(items)}개 뉴스")

    with open('output/collected_news.json', 'w', encoding='utf-8') as f:
        json.dump(collect_result, f, ensure_ascii=False, indent=2)

    print("\n=== Phase 1.5: 중복 제거 ===")
    dedup_result = remove_duplicates(items)
    deduped_items = dedup_result['unique_items']
    print(f"중복 제거 완료: {len(items)} -> {len(deduped_items)}개")

    with open('output/deduplicated_news.json', 'w', encoding='utf-8') as f:
        json.dump(dedup_result, f, ensure_ascii=False, indent=2)

    print("\n=== Phase 2: 콘텐츠 처리 (배치 요약/번역) ===")
    process_result = process_news_items(deduped_items, use_batch=True, batch_size=5)
    if not process_result['success']:
        raise Exception("요약/번역 실패")
    processed_items = process_result['items']
    print(f"처리 완료: {len(processed_items)}개 뉴스 (토큰: {process_result['statistics']['total_tokens_used']})")

    with open('output/processed_news.json', 'w', encoding='utf-8') as f:
        json.dump(process_result, f, ensure_ascii=False, indent=2)

    print("\n=== Phase 3: 데이터베이스 저장 ===")
    db = DatabaseClient()
    db.connect()
    db_result = db.insert_news_items(processed_items)
    print(f"DB 저장 완료: {db_result.get('inserted', 0)}건 삽입, {db_result.get('skipped_duplicates', 0)}건 중복 스킵")

    print("\n=== Phase 4: 뉴스레터 생성 ===")
    newsletter_result = generate_newsletter(processed_items)
    if not newsletter_result['success']:
        raise Exception(f"뉴스레터 생성 실패: {newsletter_result.get('error')}")
    html_content = newsletter_result['html_content']

    with open('output/newsletter.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"뉴스레터 생성 완료: {newsletter_result['newsletter_size']}")

    print("\n=== Phase 5: 이메일 발송 ===")
    issue_date = datetime.now().strftime('%Y-%m-%d')
    send_result = send_newsletter(html_content, issue_date)
    if not send_result.get('success'):
        raise Exception(f"이메일 발송 실패: {send_result.get('error')}")
    recipient_count = send_result.get('successful', 0)
    print(f"이메일 발송 완료: {recipient_count}명")

    print("\n=== Phase 6: 발행 기록 저장 ===")
    inserted_ids = db_result.get('inserted_ids', [])
    record_result = db.insert_newsletter(html_content, recipient_count, inserted_ids)
    print(f"뉴스레터 기록 저장 완료: ID={record_result.get('newsletter_id')}")

    db.disconnect()
    print("\n모든 작업 완료!")
    sys.exit(0)

except Exception as e:
    print(f"\n에러 발생: {str(e)}")
    import traceback
    traceback.print_exc()

    try:
        send_error_notification(type(e).__name__, str(e), datetime.now().isoformat())
        print("관리자에게 에러 알림 발송 완료")
    except:
        print("에러 알림 발송 실패")

    sys.exit(1)
PYTHON_SCRIPT

EXIT_CODE=$?

echo "========================================" | tee -a "$LOG_FILE"
echo "Finished at: $(date)" | tee -a "$LOG_FILE"
echo "Exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE
