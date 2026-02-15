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

from tools.customs.apps.rss_collector import collect_news_from_feeds
from tools.customs.apps.groq_summarizer import process_news_with_groq
from tools.customs.apps.db_client import save_news_to_db, save_newsletter_record
from tools.customs.apps.newsletter_generator import generate_newsletter
from tools.customs.apps.email_sender import send_newsletter_email

try:
    print("\n=== Phase 1: RSS 수집 ===")
    collected = collect_news_from_feeds()
    print(f"수집 완료: {len(collected)}개 뉴스")

    with open('output/collected_news.json', 'w', encoding='utf-8') as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)

    print("\n=== Phase 2: 콘텐츠 처리 (요약/번역) ===")
    processed = process_news_with_groq(collected)
    print(f"처리 완료: {len(processed)}개 뉴스")

    with open('output/processed_news.json', 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    print("\n=== Phase 3: 데이터베이스 저장 ===")
    save_news_to_db(processed)
    print("DB 저장 완료")

    print("\n=== Phase 4: 뉴스레터 생성 ===")
    html_content = generate_newsletter(processed)

    with open('output/newsletter.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"뉴스레터 생성 완료: {len(html_content)} bytes")

    print("\n=== Phase 5: 이메일 발송 ===")
    send_newsletter_email(html_content)
    print("이메일 발송 완료")

    print("\n=== Phase 6: 발행 기록 저장 ===")
    newsletter_id = save_newsletter_record(
        subject=f"AI 뉴스 다이제스트 - {datetime.now().strftime('%Y-%m-%d')}",
        recipient_count=1,
        sent_at=datetime.now()
    )
    print(f"뉴스레터 기록 저장 완료: ID={newsletter_id}")

    print("\n✅ 모든 작업 완료!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ 에러 발생: {str(e)}")
    import traceback
    traceback.print_exc()

    try:
        from tools.customs.apps.email_sender import send_error_notification
        send_error_notification(str(e), traceback.format_exc())
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
